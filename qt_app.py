#!/usr/bin/env python3
from __future__ import annotations

import sys
import csv
import platform
from dataclasses import dataclass, field
import json
import os
import sqlite3
import shutil
from pathlib import Path
from typing import Dict, List

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QSpinBox, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QFileDialog, QMessageBox, QFormLayout, QGroupBox, QStatusBar, QTabWidget,
    QDialog, QDialogButtonBox
)



@dataclass
class Produto:
    id: int | None = None
    nome: str = ""
    categoria: str = ""
    quantidade: int = 0
    unidade: str = ""


@dataclass
class FornecedorItem:
    # optional identifiers to track DB rows
    id: int | None = None
    supplier_id: int | None = None
    fornecedor: str = ""
    marca: str = ""
    preco_unitario: float = 0.0
    quantidade: int = 0
    frete: float = 0.0
    prazo: str = ""
    observacoes: str = ""

    @property
    def subtotal(self) -> float:
        return self.preco_unitario * self.quantidade

    @property
    def total(self) -> float:
        return self.subtotal + self.frete


class JanelaPrincipal(QMainWindow):
    # guard against macOS menu action calling without init (invalid stub removed)
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Comparação de Preços - Odontopediatria (Qt)")
        self.resize(1200, 760)

        # Dados
        self.produtos: List[Produto] = []
        self.fornecedores_data: Dict[str, List[FornecedorItem]] = {}
        self.current_file: Path | None = None
        self.is_dirty: bool = False
        # Banco de dados SQLite
        self.db = Database(self._default_data_path())
        self.current_file = self.db.path

        # UI
        container = QWidget()
        self.setCentralWidget(container)
        root = QVBoxLayout(container)

        # Abas: Cadastro e Filtro
        self.tabs = QTabWidget()
        root.addWidget(self.tabs)

        # Cadastro de Produto
        tab_cadastro = QWidget()
        lay_cadastro = QVBoxLayout(tab_cadastro)
        grp_produto = QGroupBox("Cadastro de Produto")
        form_prod = QFormLayout(grp_produto)
        self.ed_nome = QLineEdit()
        self.cmb_categoria = QComboBox()
        self.cmb_categoria.addItems([
            "Biossegurança", "Semiologia", "Preventiva", "Radiologia",
            "Odontopediatria", "Isolamento Absoluto", "Dentística",
            "Moldagem e Prótese", "Endodontia", "Cirurgia", "Ortodontia"
        ])
        self.spin_qtd = QSpinBox()
        self.spin_qtd.setRange(1, 100000)
        self.spin_qtd.setValue(1)
        self.cmb_unidade = QComboBox()
        self.cmb_unidade.addItems(["Unidade", "Pacote", "Caixa", "Jogo", "Kit", "Frasco", "Litro"])

        btn_add_prod = QPushButton("➕ Adicionar Produto")
        btn_add_prod.clicked.connect(self.adicionar_produto)

        form_prod.addRow("Nome:", self.ed_nome)
        form_prod.addRow("Categoria:", self.cmb_categoria)
        form_prod.addRow("Quantidade:", self.spin_qtd)
        form_prod.addRow("Unidade:", self.cmb_unidade)
        form_prod.addRow("", btn_add_prod)

        # Cadastro de Fornecedor
        grp_forn = QGroupBox("Cadastro de Fornecedores")
        form_f = QFormLayout(grp_forn)
        self.cmb_produto_sel = QComboBox()
        self.ed_fornecedor = QLineEdit()
        self.ed_marca = QLineEdit()
        self.ed_preco = QLineEdit()
        self.ed_frete = QLineEdit()
        self.ed_frete.setText("0")
        self.ed_prazo = QLineEdit()
        self.ed_prazo.setText("3 dias")
        self.ed_obs = QLineEdit()
        btn_add_forn = QPushButton("➕ Adicionar Fornecedor")
        btn_add_forn.clicked.connect(self.adicionar_fornecedor)

        # product selector (no inline edit/delete here - Lista tab centraliza edição/remoção)
        form_f.addRow("Produto:", self.cmb_produto_sel)
        form_f.addRow("Fornecedor:", self.ed_fornecedor)
        form_f.addRow("Marca:", self.ed_marca)
        form_f.addRow("Preço Unitário (R$):", self.ed_preco)
        form_f.addRow("Frete (R$):", self.ed_frete)
        form_f.addRow("Prazo:", self.ed_prazo)
        form_f.addRow("Observações:", self.ed_obs)
        form_f.addRow("", btn_add_forn)

        # Monta tab Cadastro
        lay_cadastro.addWidget(grp_produto)
        lay_cadastro.addWidget(grp_forn)
        self.tabs.addTab(tab_cadastro, "Cadastro")

        # Tab Lista (produtos / fornecedores)
        tab_lista = QWidget()
        lay_lista = QVBoxLayout(tab_lista)
        self.lista_tabs = QTabWidget()

        # Produtos tab
        produtos_tab = QWidget()
        lay_produtos = QVBoxLayout(produtos_tab)
        prod_bar = QHBoxLayout()
        btn_edit_prod = QPushButton("✏️ Editar Produto")
        btn_edit_prod.clicked.connect(self.edit_product_from_list)
        btn_del_prod = QPushButton("🗑️ Deletar Produto")
        btn_del_prod.clicked.connect(self.delete_product_from_list)
        prod_bar.addWidget(btn_edit_prod)
        prod_bar.addWidget(btn_del_prod)
        lay_produtos.addLayout(prod_bar)
        self.prod_table = QTableWidget(0, 5)
        self.prod_table.setHorizontalHeaderLabels(["ID", "Nome", "Categoria", "Qtd", "Unidade"])
        self.prod_table.hideColumn(0)
        lay_produtos.addWidget(self.prod_table)
        self.lista_tabs.addTab(produtos_tab, "Produtos")

        # Fornecedores tab
        fornecedores_tab = QWidget()
        lay_fornecedores = QVBoxLayout(fornecedores_tab)
        forn_bar = QHBoxLayout()
        btn_edit_forn = QPushButton("✏️ Editar Fornecedor")
        btn_edit_forn.clicked.connect(self.edit_supplier_from_list)
        btn_del_forn = QPushButton("🗑️ Deletar Fornecedor")
        btn_del_forn.clicked.connect(self.delete_supplier_from_list)
        forn_bar.addWidget(btn_edit_forn)
        forn_bar.addWidget(btn_del_forn)
        lay_fornecedores.addLayout(forn_bar)
        self.forn_table = QTableWidget(0, 3)
        self.forn_table.setHorizontalHeaderLabels(["ID", "Fornecedor", "#Ofertas"])
        self.forn_table.hideColumn(0)
        lay_fornecedores.addWidget(self.forn_table)
        self.lista_tabs.addTab(fornecedores_tab, "Fornecedores")

        lay_lista.addWidget(self.lista_tabs)
        self.tabs.addTab(tab_lista, "Lista")

        # Tab Filtro
        tab_filtro = QWidget()
        lay_filtro = QVBoxLayout(tab_filtro)
        bar_filtro = QHBoxLayout()
        lbl_prod = QLabel("Produto:")
        self.cmb_filtro_produto = QComboBox()
        btn_melhor = QPushButton("🏆 Melhor valor final")
        btn_melhor.clicked.connect(self.mostrar_melhor_opcao)
        btn_export = QPushButton("💾 Exportar CSV")
        btn_export.clicked.connect(self.exportar_csv)
        btn_limpar = QPushButton("🗑️ Limpar Tudo")
        btn_limpar.clicked.connect(self.limpar_tudo)

    # filtro bar: apenas seleção e ações não-destrutivas
        bar_filtro.addWidget(lbl_prod)
        bar_filtro.addWidget(self.cmb_filtro_produto, 1)
        bar_filtro.addWidget(btn_melhor)
        bar_filtro.addWidget(btn_export)
        bar_filtro.addWidget(btn_limpar)

        self.table = QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels([
            "Produto", "Fornecedor", "Marca", "Preço Unit.", "Qtd",
            "Subtotal", "Frete", "Total", "Prazo"
        ])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setMinimumSectionSize(80)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)

        self.cmb_filtro_produto.currentTextChanged.connect(self._refresh_filtered_table)

        lay_filtro.addLayout(bar_filtro)
        lay_filtro.addWidget(self.table)
        self.tabs.addTab(tab_filtro, "Filtro")

        # Menu
        self._criar_menu()

        # Status bar
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Pronto")

        # Carregar dados do banco
        self._load_from_db_to_memory()

    # ======= Persistência =======
    def mark_dirty(self, dirty: bool = True):
        self.is_dirty = dirty
        title = "Comparação de Preços - Odontopediatria (Qt)"
        if self.current_file:
            title += f" — {self.current_file.name}"
        if self.is_dirty:
            title += " *"
        self.setWindowTitle(title)
        # Persistência automática em segundo plano
        if dirty:
            try:
                self._autosave_silent()
            except Exception:
                pass

    def _load_from_db_to_memory(self):
        self.produtos = self.db.list_products()
        self.fornecedores_data = {p.nome: self.db.list_offers_by_product(p.nome) for p in self.produtos}
        self._refresh_produtos_combo()
        # refresh new lists
        try:
            self._refresh_prod_list()
            self._refresh_forn_list()
        except Exception:
            pass
        self.table.setRowCount(0)
        if self.cmb_filtro_produto.currentText():
            self._refresh_filtered_table()
        self.mark_dirty(False)

    def _autosave_now(self):
        """Garante que o banco está com commit persistido e caminho atual definido."""
        try:
            if self.db and self.db.conn:
                self.db.conn.commit()
            if not self.current_file:
                self.current_file = self.db.path
        except Exception:
            pass

    def file_new(self):
        if not self._maybe_save_changes():
            return
        path, _ = QFileDialog.getSaveFileName(self, "Criar banco", "", "Banco (*.sqlite)")
        if not path:
            return
        if not path.lower().endswith('.sqlite'):
            path += '.sqlite'
        try:
            self.db = Database(Path(path))
            self.current_file = Path(path)
            self._load_from_db_to_memory()
            self.statusBar().showMessage(f"Banco criado: {self.current_file}", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao criar banco:\n{e}")

    def file_open(self):
        if not self._maybe_save_changes():
            return
        path, _ = QFileDialog.getOpenFileName(self, "Abrir banco", "", "Banco (*.sqlite)")
        if not path:
            return
        try:
            self.db = Database(Path(path))
            self.current_file = Path(path)
            self._load_from_db_to_memory()
            self.statusBar().showMessage(f"Banco carregado: {self.current_file}", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao abrir banco:\n{e}")

    def file_save_as(self):
        path, _ = QFileDialog.getSaveFileName(self, "Salvar banco como", "", "Banco (*.sqlite)")
        if not path:
            return False
        if not path.lower().endswith(".sqlite"):
            path += ".sqlite"
        self.current_file = Path(path)
        return self._write_current_file()

    def file_save(self):
        if not self.current_file:
            return self.file_save_as()
        return self._write_current_file()

    def _write_current_file(self):
        try:
            # Salvar/cópia física do banco atual
            if self.db and self.db.path and self.current_file:
                if Path(self.db.path) != self.current_file:
                    shutil.copyfile(self.db.path, self.current_file)
                self.db = Database(self.current_file)
            self.mark_dirty(False)
            self.statusBar().showMessage(f"Banco salvo: {self.current_file}", 3000)
            return True
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao salvar banco:\n{e}")
            return False

    def _autosave_silent(self):
        """Salva automaticamente no arquivo padrão, sem diálogos."""
        # DB já grava a cada operação; apenas garante que temos um caminho atual
        if not self.current_file:
            self.current_file = self._default_data_path()

    def _load_default_if_present(self):
        path = self._default_data_path()
        if path.exists():
            self.db = Database(path)
            self.current_file = path
            self._load_from_db_to_memory()
            self.statusBar().showMessage(f"Banco carregado: {self.current_file}", 3000)
        else:
            fb = self._fallback_user_data_path()
            if fb.exists():
                self.db = Database(fb)
                self.current_file = fb
                self._load_from_db_to_memory()
                self.statusBar().showMessage(f"Banco carregado: {self.current_file}", 3000)

    def _default_data_path(self) -> Path:
        # Preferir pasta de instalação (ao lado do executável/script)
        if getattr(sys, 'frozen', False):
            app_dir = Path(sys.executable).resolve().parent
        else:
            app_dir = Path(__file__).resolve().parent
        target = app_dir / 'dados.sqlite'
        return target

    def _fallback_user_data_path(self) -> Path:
        system = platform.system()
        if system == 'Darwin':
            base = Path.home() / 'Library' / 'Application Support' / 'OdontoPrice'
        elif system == 'Windows':
            base = Path(os.environ.get('APPDATA', str(Path.home() / 'AppData' / 'Roaming'))) / 'OdontoPrice'
        else:
            base = Path.home() / '.local' / 'share' / 'odonto_price'
        return base / 'dados.json'

    def _maybe_save_changes(self) -> bool:
        if not self.is_dirty:
            return True
        resp = QMessageBox.question(
            self, "Salvar alterações?", "Deseja salvar as alterações do projeto?",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            QMessageBox.Yes,
        )
        if resp == QMessageBox.Cancel:
            return False
        if resp == QMessageBox.Yes:
            return bool(self.file_save())
        return True

    def _criar_menu(self):
        mbar = self.menuBar()
        arq = mbar.addMenu("Arquivo")
        act_new = QAction("Novo", self)
        act_new.setShortcut("Ctrl+N")
        act_new.triggered.connect(self.file_new)
        act_open = QAction("Abrir…", self)
        act_open.setShortcut("Ctrl+O")
        act_open.triggered.connect(self.file_open)
        act_save = QAction("Salvar", self)
        act_save.setShortcut("Ctrl+S")
        act_save.triggered.connect(self.file_save)
        act_save_as = QAction("Salvar como…", self)
        act_save_as.triggered.connect(self.file_save_as)
        arq.addAction(act_new)
        arq.addAction(act_open)
        arq.addSeparator()
        arq.addAction(act_save)
        arq.addAction(act_save_as)
        arq.addSeparator()
        act_export = QAction("Exportar CSV", self)
        act_export.triggered.connect(self.exportar_csv)
        act_quit = QAction("Sair", self)
        act_quit.triggered.connect(self.close)
        arq.addAction(act_export)
        arq.addSeparator()
        arq.addAction(act_quit)

    def adicionar_produto(self):
        nome = self.ed_nome.text().strip()
        cat = self.cmb_categoria.currentText().strip()
        qtd = int(self.spin_qtd.value())
        un = self.cmb_unidade.currentText().strip()

        if not nome or not cat:
            QMessageBox.warning(self, "Atenção", "Preencha o nome e a categoria do produto!")
            return

        self.db.upsert_product(nome, cat, qtd, un)
        self._autosave_now()
        self._load_from_db_to_memory()
        self.ed_nome.clear()
        self.spin_qtd.setValue(1)
        self.statusBar().showMessage(f"Produto '{nome}' adicionado", 3000)
        self.mark_dirty(True)

    def _refresh_produtos_combo(self):
        nomes = [p.nome for p in self.produtos]
        self.cmb_produto_sel.blockSignals(True)
        self.cmb_produto_sel.clear()
        self.cmb_produto_sel.addItems(nomes)
        self.cmb_produto_sel.blockSignals(False)
        self.cmb_filtro_produto.blockSignals(True)
        self.cmb_filtro_produto.clear()
        self.cmb_filtro_produto.addItems(nomes)
        self.cmb_filtro_produto.blockSignals(False)
        self._refresh_filtered_table()

    def adicionar_fornecedor(self):
        produto = self.cmb_produto_sel.currentText()
        fornecedor = self.ed_fornecedor.text().strip()
        marca = self.ed_marca.text().strip()
        preco_txt = self.ed_preco.text().strip().replace(',', '.')
        frete_txt = self.ed_frete.text().strip().replace(',', '.')
        prazo = self.ed_prazo.text().strip()
        obs = self.ed_obs.text().strip()

        if not produto:
            QMessageBox.warning(self, "Atenção", "Selecione um produto!")
            return
        if not fornecedor or not preco_txt:
            QMessageBox.warning(self, "Atenção", "Preencha fornecedor e preço!")
            return
        try:
            preco = float(preco_txt)
            frete = float(frete_txt) if frete_txt else 0.0
        except Exception:
            QMessageBox.critical(self, "Erro", "Preço e Frete devem ser números válidos")
            return

        qtd = next((p.quantidade for p in self.produtos if p.nome == produto), 1)
        self.db.add_offer(produto, fornecedor, marca, preco, qtd, frete, prazo, obs)
        self._autosave_now()
        self._load_from_db_to_memory()

        self.ed_fornecedor.clear()
        self.ed_marca.clear()
        self.ed_preco.clear()
        self.ed_frete.setText("0")
        self.ed_obs.clear()
        self.statusBar().showMessage(f"Fornecedor '{fornecedor}' adicionado para '{produto}'", 3000)
        self.mark_dirty(True)

    # ======= Produtos: editar / deletar =======
    def edit_selected_product(self):
        # prefer product selector in cadastro (cmb_produto_sel) if present, otherwise filter combo
        nome = (self.cmb_produto_sel.currentText() if getattr(self, 'cmb_produto_sel', None) else '') or (self.cmb_filtro_produto.currentText() if getattr(self, 'cmb_filtro_produto', None) else '') or ''
        if not nome:
            QMessageBox.warning(self, "Atenção", "Selecione um produto para editar")
            return
        prod = next((p for p in self.produtos if p.nome == nome), None)
        if not prod:
            QMessageBox.warning(self, "Atenção", "Produto não encontrado")
            return
        result = self._show_edit_product_dialog(prod)
        if not result:
            return
        try:
            new_name = result['name']
            category = result['category']
            quantity = int(result['quantity'])
            unit = result['unit']
        except Exception:
            QMessageBox.critical(self, "Erro", "Valores inválidos")
            return
        ok = self.db.update_product(prod.nome, new_name, category, quantity, unit)
        if ok:
            self._load_from_db_to_memory()
            self.statusBar().showMessage("Produto atualizado", 3000)
            self.mark_dirty(True)
        else:
            QMessageBox.critical(self, "Erro", "Falha ao atualizar produto")

    def delete_selected_product(self):
        # prefer product selector in cadastro (cmb_produto_sel) if present, otherwise filter combo
        nome = (self.cmb_produto_sel.currentText() if getattr(self, 'cmb_produto_sel', None) else '') or (self.cmb_filtro_produto.currentText() if getattr(self, 'cmb_filtro_produto', None) else '') or ''
        if not nome:
            QMessageBox.warning(self, "Atenção", "Selecione um produto para deletar")
            return
        count = self.db.count_offers_for_product(nome)
        if count > 0:
            resp = QMessageBox.question(
                self,
                "Confirmação",
                f"O produto '{nome}' tem {count} fornecedor(es) associado(s).\nDeseja realmente deletar o produto e todas as ofertas relacionadas?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if resp != QMessageBox.Yes:
                return
        else:
            if QMessageBox.question(self, "Confirmação", f"Deseja deletar o produto '{nome}'?") != QMessageBox.Yes:
                return
        ok = self.db.delete_product(nome)
        if ok:
            self._load_from_db_to_memory()
            self.statusBar().showMessage("Produto deletado", 3000)
            self.mark_dirty(True)
        else:
            QMessageBox.critical(self, "Erro", "Falha ao deletar produto")

    def _show_edit_product_dialog(self, prod: Produto):
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Editar Produto — {prod.nome}")
        layout = QVBoxLayout(dlg)
        form = QFormLayout()
        ed_name = QLineEdit(); ed_name.setText(prod.nome)
        cmb_cat = QComboBox()
        cmb_cat.addItems([
            "Biossegurança", "Semiologia", "Preventiva", "Radiologia",
            "Odontopediatria", "Isolamento Absoluto", "Dentística",
            "Moldagem e Prótese", "Endodontia", "Cirurgia", "Ortodontia"
        ])
        if prod.categoria:
            idx = cmb_cat.findText(prod.categoria)
            if idx >= 0:
                cmb_cat.setCurrentIndex(idx)
        spin_q = QSpinBox(); spin_q.setRange(1, 100000); spin_q.setValue(prod.quantidade)
        cmb_unit = QComboBox(); cmb_unit.addItems(["Unidade", "Pacote", "Caixa", "Jogo", "Kit", "Frasco", "Litro"]) 
        idxu = cmb_unit.findText(prod.unidade)
        if idxu >= 0:
            cmb_unit.setCurrentIndex(idxu)

        form.addRow("Nome:", ed_name)
        form.addRow("Categoria:", cmb_cat)
        form.addRow("Quantidade:", spin_q)
        form.addRow("Unidade:", cmb_unit)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        layout.addWidget(buttons)
        if dlg.exec() != QDialog.Accepted:
            return None
        return {
            'name': ed_name.text().strip(),
            'category': cmb_cat.currentText().strip(),
            'quantity': spin_q.value(),
            'unit': cmb_unit.currentText().strip(),
        }

    # ===== handlers for Lista tab =====
    def edit_product_from_list(self):
        if not hasattr(self, 'prod_table'):
            return
        row = self.prod_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione um produto na lista para editar")
            return
        name_item = self.prod_table.item(row, 1)
        if not name_item:
            QMessageBox.warning(self, "Atenção", "Produto inválido")
            return
        name = name_item.text()
        prod = next((p for p in self.produtos if p.nome == name), None)
        if not prod:
            QMessageBox.warning(self, "Atenção", "Produto não encontrado")
            return
        result = self._show_edit_product_dialog(prod)
        if not result:
            return
        try:
            new_name = result['name']
            category = result['category']
            quantity = int(result['quantity'])
            unit = result['unit']
        except Exception:
            QMessageBox.critical(self, "Erro", "Valores inválidos")
            return
        ok = self.db.update_product(prod.nome, new_name, category, quantity, unit)
        if ok:
            self._load_from_db_to_memory()
            self.statusBar().showMessage("Produto atualizado", 3000)
            self.mark_dirty(True)
        else:
            QMessageBox.critical(self, "Erro", "Falha ao atualizar produto (talvez nome já exista)")

    def delete_product_from_list(self):
        if not hasattr(self, 'prod_table'):
            return
        row = self.prod_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione um produto na lista para deletar")
            return
        name_item = self.prod_table.item(row, 1)
        if not name_item:
            QMessageBox.warning(self, "Atenção", "Produto inválido")
            return
        name = name_item.text()
        count = self.db.count_offers_for_product(name)
        if count > 0:
            resp = QMessageBox.question(
                self,
                "Confirmação",
                f"O produto '{name}' tem {count} fornecedor(es) associado(s).\nDeseja realmente deletar o produto e todas as ofertas relacionadas?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if resp != QMessageBox.Yes:
                return
        else:
            if QMessageBox.question(self, "Confirmação", f"Deseja deletar o produto '{name}'?") != QMessageBox.Yes:
                return
        ok = self.db.delete_product(name)
        if ok:
            self._load_from_db_to_memory()
            self.statusBar().showMessage("Produto deletado", 3000)
            self.mark_dirty(True)
        else:
            QMessageBox.critical(self, "Erro", "Falha ao deletar produto")

    def edit_supplier_from_list(self):
        if not hasattr(self, 'forn_table'):
            return
        row = self.forn_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione um fornecedor na lista para editar")
            return
        id_item = self.forn_table.item(row, 0)
        name_item = self.forn_table.item(row, 1)
        if not id_item or not name_item:
            QMessageBox.warning(self, "Atenção", "Fornecedor inválido")
            return
        sid = id_item.data(Qt.UserRole) or int(id_item.text())
        name = name_item.text()
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Editar Fornecedor — {name}")
        layout = QVBoxLayout(dlg)
        form = QFormLayout()
        ed_name = QLineEdit(); ed_name.setText(name)
        form.addRow("Nome:", ed_name)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        layout.addWidget(buttons)
        if dlg.exec() != QDialog.Accepted:
            return
        new_name = ed_name.text().strip()
        if not new_name:
            QMessageBox.warning(self, "Atenção", "Nome não pode ficar vazio")
            return
        ok = self.db.update_supplier(int(sid), new_name)
        if ok:
            self._load_from_db_to_memory()
            self.statusBar().showMessage("Fornecedor atualizado", 3000)
            self.mark_dirty(True)
        else:
            QMessageBox.critical(self, "Erro", "Falha ao atualizar fornecedor (nome talvez conflitante)")

    def delete_supplier_from_list(self):
        if not hasattr(self, 'forn_table'):
            return
        row = self.forn_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione um fornecedor na lista para deletar")
            return
        id_item = self.forn_table.item(row, 0)
        name_item = self.forn_table.item(row, 1)
        if not id_item or not name_item:
            QMessageBox.warning(self, "Atenção", "Fornecedor inválido")
            return
        sid = id_item.data(Qt.UserRole) or int(id_item.text())
        name = name_item.text()
        count = self.db.count_offers_for_supplier(int(sid))
        if count > 0:
            resp = QMessageBox.question(
                self,
                "Confirmação",
                f"O fornecedor '{name}' tem {count} oferta(s) associadas.\nDeseja realmente deletar o fornecedor e todas as ofertas relacionadas?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if resp != QMessageBox.Yes:
                return
        else:
            if QMessageBox.question(self, "Confirmação", f"Deseja deletar o fornecedor '{name}'?") != QMessageBox.Yes:
                return
        ok = self.db.delete_supplier(int(sid))
        if ok:
            self._load_from_db_to_memory()
            self.statusBar().showMessage("Fornecedor deletado", 3000)
            self.mark_dirty(True)
        else:
            QMessageBox.critical(self, "Erro", "Falha ao deletar fornecedor")

    def _append_table_row(self, produto: str, f: FornecedorItem):
        r = self.table.rowCount()
        self.table.insertRow(r)
        vals = [
            produto,
            f.fornecedor,
            f.marca,
            f"R$ {f.preco_unitario:.2f}",
            str(f.quantidade),
            f"R$ {f.subtotal:.2f}",
            f"R$ {f.frete:.2f}",
            f"R$ {f.total:.2f}",
            f.prazo,
        ]
        for c, val in enumerate(vals):
            item = QTableWidgetItem(val)
            # store offer id in the first column's user role for later actions
            if c == 0 and f.id is not None:
                item.setData(Qt.UserRole, int(f.id))
            if c in (3, 5, 6, 7):
                item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(r, c, item)

    def mostrar_melhor_opcao(self):
        # Prioriza a aba de filtro
        produto = self.cmb_filtro_produto.currentText() or self.cmb_produto_sel.currentText()
        if not produto:
            QMessageBox.warning(self, "Atenção", "Selecione um produto com fornecedores!")
            return
        itens = self.db.list_offers_by_product(produto)
        if not itens:
            QMessageBox.warning(self, "Atenção", "Nenhum fornecedor cadastrado!")
            return
        melhor = min(itens, key=lambda x: x.total)
        diffs = []
        for it in sorted(itens, key=lambda x: x.total):
            if it is melhor:
                continue
            diffs.append(f"• {it.fornecedor}: R$ {it.total:.2f} (+R$ {it.total - melhor.total:.2f})")
        msg = (
            f"🏆 MELHOR OPÇÃO PARA: {produto}\n\n"
            f"Fornecedor: {melhor.fornecedor}\n"
            f"Marca: {melhor.marca}\n"
            f"Preço Total: R$ {melhor.total:.2f}\n"
            f"  • Unitário: R$ {melhor.preco_unitario:.2f}\n"
            f"  • Quantidade: {melhor.quantidade}\n"
            f"  • Subtotal: R$ {melhor.subtotal:.2f}\n"
            f"  • Frete: R$ {melhor.frete:.2f}\n"
            f"Prazo: {melhor.prazo}\n\n"
            f"📊 COMPARAÇÃO COM OUTROS:\n" + ("\n".join(diffs) if diffs else "—")
        )
        QMessageBox.information(self, "Melhor Opção", msg)

    def exportar_csv(self):
        if not self.produtos:
            QMessageBox.warning(self, "Atenção", "Nenhum produto cadastrado!")
            return
        dirpath = QFileDialog.getExistingDirectory(self, "Selecione a pasta para salvar")
        if not dirpath:
            return
        pasta = Path(dirpath)

        for prod in self.produtos:
            itens = self.db.list_offers_by_product(prod.nome)
            if not itens:
                continue
            caminho = pasta / f"{self._sanitize_filename(prod.nome) }.csv"
            with open(caminho, 'w', newline='', encoding='utf-8-sig') as fp:
                w = csv.writer(fp)
                w.writerow(['PRODUTO', prod.nome])
                w.writerow(['CATEGORIA', prod.categoria])
                w.writerow(['QUANTIDADE', prod.quantidade])
                w.writerow(['UNIDADE', prod.unidade])
                w.writerow([])
                w.writerow(['Fornecedor', 'Marca', 'Preco_Unitario', 'Quantidade', 'Subtotal', 'Frete', 'Total', 'Prazo', 'Observacoes'])
                for it in sorted(itens, key=lambda x: x.total):
                    w.writerow([
                        it.fornecedor, it.marca, it.preco_unitario, it.quantidade,
                        it.subtotal, it.frete, it.total, it.prazo, it.observacoes
                    ])
                w.writerow([])
                melhor = min(itens, key=lambda x: x.total)
                w.writerow(['MELHOR_OPCAO', melhor.fornecedor])
                w.writerow(['MENOR_PRECO', melhor.total])
        QMessageBox.information(self, "Sucesso", f"CSV(s) exportados para:\n{pasta}")

    def limpar_tudo(self):
        if QMessageBox.question(self, "Confirmação", "Deseja realmente limpar todos os dados?") != QMessageBox.Yes:
            return
        # Limpa banco atual
        if self.db and self.db.path:
            try:
                Path(self.db.path).unlink(missing_ok=True)
            except Exception:
                pass
            self.db = Database(self._default_data_path())
        self._load_from_db_to_memory()
        self.statusBar().showMessage("Dados limpos", 3000)
        self.current_file = None
        self.mark_dirty(True)

    def closeEvent(self, event):
        try:
            # Salvar silenciosamente antes de fechar
            self._autosave_silent()
        except Exception:
            pass
        super().closeEvent(event)

    def _refresh_filtered_table(self):
        self.table.setRowCount(0)
        produto = self.cmb_filtro_produto.currentText()
        if not produto:
            return
        for it in self.db.list_offers_by_product(produto):
            self._append_table_row(produto, it)

    # ===== Refresh lists =====
    def _refresh_prod_list(self):
        if not hasattr(self, 'prod_table'):
            return
        self.prod_table.setRowCount(0)
        for p in self.produtos:
            r = self.prod_table.rowCount()
            self.prod_table.insertRow(r)
            id_item = QTableWidgetItem(str(p.id) if p.id is not None else "")
            id_item.setData(Qt.UserRole, int(p.id) if p.id is not None else None)
            name_item = QTableWidgetItem(p.nome)
            cat_item = QTableWidgetItem(p.categoria)
            qtd_item = QTableWidgetItem(str(p.quantidade))
            unit_item = QTableWidgetItem(p.unidade)
            self.prod_table.setItem(r, 0, id_item)
            self.prod_table.setItem(r, 1, name_item)
            self.prod_table.setItem(r, 2, cat_item)
            self.prod_table.setItem(r, 3, qtd_item)
            self.prod_table.setItem(r, 4, unit_item)

    def _refresh_forn_list(self):
        if not hasattr(self, 'forn_table'):
            return
        self.forn_table.setRowCount(0)
        for sid, name in self.db.list_suppliers():
            r = self.forn_table.rowCount()
            self.forn_table.insertRow(r)
            id_item = QTableWidgetItem(str(sid))
            id_item.setData(Qt.UserRole, int(sid))
            name_item = QTableWidgetItem(name)
            count_item = QTableWidgetItem(str(self.db.count_offers_for_supplier(int(sid))))
            self.forn_table.setItem(r, 0, id_item)
            self.forn_table.setItem(r, 1, name_item)
            self.forn_table.setItem(r, 2, count_item)

    def edit_selected_offer(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione uma oferta na tabela para editar")
            return
        item = self.table.item(row, 0)
        if item is None:
            QMessageBox.warning(self, "Atenção", "Não foi possível identificar a oferta selecionada")
            return
        offer_id = item.data(Qt.UserRole)
        if not offer_id:
            QMessageBox.warning(self, "Atenção", "ID da oferta não disponível")
            return
        info = self.db.get_offer_by_id(int(offer_id))
        if not info:
            QMessageBox.warning(self, "Atenção", "Oferta não encontrada no banco")
            return
        product_name, fi = info
        result = self._show_edit_offer_dialog(product_name, fi)
        if not result:
            return
        try:
            brand = result['brand']
            unit_price = float(result['unit_price'])
            quantity = int(result['quantity'])
            freight = float(result['freight'])
            deadline = result['deadline']
            notes = result['notes']
        except Exception:
            QMessageBox.critical(self, "Erro", "Valores inválidos")
            return
        ok = self.db.update_offer(int(offer_id), brand, unit_price, quantity, freight, deadline, notes)
        if ok:
            self._load_from_db_to_memory()
            self.statusBar().showMessage("Oferta atualizada", 3000)
            self.mark_dirty(True)
        else:
            QMessageBox.critical(self, "Erro", "Falha ao atualizar oferta")

    def delete_selected_offer(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione uma oferta na tabela para deletar")
            return
        item = self.table.item(row, 0)
        if item is None:
            QMessageBox.warning(self, "Atenção", "Não foi possível identificar a oferta selecionada")
            return
        offer_id = item.data(Qt.UserRole)
        if not offer_id:
            QMessageBox.warning(self, "Atenção", "ID da oferta não disponível")
            return
        if QMessageBox.question(self, "Confirmação", "Deseja realmente deletar a oferta selecionada?") != QMessageBox.Yes:
            return
        ok = self.db.delete_offer(int(offer_id))
        if ok:
            self._load_from_db_to_memory()
            self.statusBar().showMessage("Oferta deletada", 3000)
            self.mark_dirty(True)
        else:
            QMessageBox.critical(self, "Erro", "Falha ao deletar oferta")

    def _show_edit_offer_dialog(self, product_name: str, fi: FornecedorItem):
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Editar Oferta — {product_name} — {fi.fornecedor}")
        layout = QVBoxLayout(dlg)
        form = QFormLayout()
        ed_brand = QLineEdit()
        ed_brand.setText(fi.marca)
        ed_price = QLineEdit()
        ed_price.setText(f"{fi.preco_unitario:.2f}")
        spin_qtd = QSpinBox()
        spin_qtd.setRange(1, 100000)
        spin_qtd.setValue(fi.quantidade)
        ed_frete = QLineEdit()
        ed_frete.setText(f"{fi.frete:.2f}")
        ed_deadline = QLineEdit()
        ed_deadline.setText(fi.prazo)
        ed_notes = QLineEdit()
        ed_notes.setText(fi.observacoes)

        form.addRow("Marca:", ed_brand)
        form.addRow("Preço Unitário (R$):", ed_price)
        form.addRow("Quantidade:", spin_qtd)
        form.addRow("Frete (R$):", ed_frete)
        form.addRow("Prazo:", ed_deadline)
        form.addRow("Observações:", ed_notes)

        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        layout.addWidget(buttons)

        if dlg.exec() != QDialog.Accepted:
            return None
        return {
            'brand': ed_brand.text().strip(),
            'unit_price': ed_price.text().strip().replace(',', '.'),
            'quantity': spin_qtd.value(),
            'freight': ed_frete.text().strip().replace(',', '.'),
            'deadline': ed_deadline.text().strip(),
            'notes': ed_notes.text().strip(),
        }


class Database:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.conn = sqlite3.connect(self.path)
        self.conn.execute('PRAGMA foreign_keys = ON;')
        self.conn.execute('PRAGMA journal_mode = WAL;')
        self.conn.execute('PRAGMA synchronous = NORMAL;')
        self._init_schema()

    def _init_schema(self):
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                category TEXT,
                quantity INTEGER NOT NULL,
                unit TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS offers (
                id INTEGER PRIMARY KEY,
                product_id INTEGER NOT NULL,
                supplier_id INTEGER NOT NULL,
                brand TEXT,
                unit_price REAL NOT NULL,
                quantity INTEGER NOT NULL,
                freight REAL NOT NULL,
                deadline TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE,
                FOREIGN KEY(supplier_id) REFERENCES suppliers(id) ON DELETE CASCADE
            );
            """
        )
        cur.execute("CREATE INDEX IF NOT EXISTS idx_offers_product ON offers(product_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_offers_supplier ON offers(supplier_id);")
        self.conn.commit()

    def upsert_product(self, name: str, category: str, quantity: int, unit: str) -> int:
        cur = self.conn.cursor()
        cur.execute("SELECT id FROM products WHERE name = ?", (name,))
        row = cur.fetchone()
        if row:
            cur.execute(
                "UPDATE products SET category=?, quantity=?, unit=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (category, quantity, unit, row[0]),
            )
            self.conn.commit()
            return row[0]
        cur.execute(
            "INSERT INTO products(name, category, quantity, unit) VALUES (?, ?, ?, ?)",
            (name, category, quantity, unit),
        )
        self.conn.commit()
        return cur.lastrowid

    def get_product_quantity(self, name: str) -> int | None:
        cur = self.conn.cursor()
        cur.execute("SELECT quantity FROM products WHERE name = ?", (name,))
        row = cur.fetchone()
        return int(row[0]) if row else None

    def upsert_supplier(self, name: str) -> int:
        cur = self.conn.cursor()
        cur.execute("SELECT id FROM suppliers WHERE name = ?", (name,))
        row = cur.fetchone()
        if row:
            return row[0]
        cur.execute("INSERT INTO suppliers(name) VALUES (?)", (name,))
        self.conn.commit()
        return cur.lastrowid

    def add_offer(self, product_name: str, supplier_name: str, brand: str, unit_price: float, quantity: int, freight: float, deadline: str, notes: str):
        pid = self.upsert_product(product_name, '', quantity, '')
        sid = self.upsert_supplier(supplier_name)
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO offers(product_id, supplier_id, brand, unit_price, quantity, freight, deadline, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (pid, sid, brand, unit_price, quantity, freight, deadline, notes),
        )
        self.conn.commit()

    def list_products(self) -> List[Produto]:
        cur = self.conn.cursor()
        cur.execute("SELECT id, name, category, quantity, unit FROM products ORDER BY name COLLATE NOCASE")
        rows = cur.fetchall()
        return [Produto(id=int(r[0]), nome=r[1], categoria=r[2] or '', quantidade=int(r[3]), unidade=r[4] or 'Unidade') for r in rows]

    def list_offers_by_product(self, product_name: str) -> List[FornecedorItem]:
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT o.id as offer_id, s.id as supplier_id, s.name as fornecedor,
                   o.brand, o.unit_price, o.quantity, o.freight, o.deadline, o.notes
            FROM offers o
            JOIN products p ON p.id = o.product_id
            JOIN suppliers s ON s.id = o.supplier_id
            WHERE p.name = ?
            ORDER BY (o.unit_price * o.quantity + o.freight) ASC
            """,
            (product_name,),
        )
        rows = cur.fetchall()
        items: List[FornecedorItem] = []
        for r in rows:
            # r: offer_id, supplier_id, fornecedor, brand, unit_price, quantity, freight, deadline, notes
            items.append(FornecedorItem(
                id=int(r[0]) if r[0] is not None else None,
                supplier_id=int(r[1]) if r[1] is not None else None,
                fornecedor=r[2] or '',
                marca=r[3] or '',
                preco_unitario=float(r[4]),
                quantidade=int(r[5]),
                frete=float(r[6]),
                prazo=r[7] or '',
                observacoes=r[8] or ''
            ))
        return items

    # Suppliers management
    def list_suppliers(self) -> List[tuple]:
        cur = self.conn.cursor()
        cur.execute("SELECT id, name FROM suppliers ORDER BY name COLLATE NOCASE")
        return cur.fetchall()

    def count_offers_for_supplier(self, supplier_id: int) -> int:
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM offers WHERE supplier_id = ?", (supplier_id,))
        row = cur.fetchone()
        return int(row[0]) if row else 0

    def update_supplier(self, supplier_id: int, new_name: str) -> bool:
        cur = self.conn.cursor()
        try:
            cur.execute("UPDATE suppliers SET name = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (new_name, supplier_id))
            self.conn.commit()
            return cur.rowcount > 0
        except sqlite3.IntegrityError:
            return False

    def delete_supplier(self, supplier_id: int) -> bool:
        cur = self.conn.cursor()
        cur.execute("DELETE FROM suppliers WHERE id = ?", (supplier_id,))
        self.conn.commit()
        return cur.rowcount > 0

    def get_offer_by_id(self, offer_id: int):
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT o.id, o.product_id, p.name as product_name, o.supplier_id, s.name as supplier_name,
                   o.brand, o.unit_price, o.quantity, o.freight, o.deadline, o.notes
            FROM offers o
            JOIN products p ON p.id = o.product_id
            JOIN suppliers s ON s.id = o.supplier_id
            WHERE o.id = ?
            """,
            (offer_id,)
        )
        row = cur.fetchone()
        if not row:
            return None
        # map to FornecedorItem and include product name
        fi = FornecedorItem(
            id=int(row[0]),
            supplier_id=int(row[3]) if row[3] is not None else None,
            fornecedor=row[4] or '',
            marca=row[5] or '',
            preco_unitario=float(row[6]),
            quantidade=int(row[7]),
            frete=float(row[8]),
            prazo=row[9] or '',
            observacoes=row[10] or ''
        )
        return (row[2], fi)

    def delete_offer(self, offer_id: int) -> bool:
        cur = self.conn.cursor()
        cur.execute("DELETE FROM offers WHERE id = ?", (offer_id,))
        self.conn.commit()
        return cur.rowcount > 0

    def update_offer(self, offer_id: int, brand: str, unit_price: float, quantity: int, freight: float, deadline: str, notes: str) -> bool:
        cur = self.conn.cursor()
        cur.execute(
            """
            UPDATE offers
            SET brand = ?, unit_price = ?, quantity = ?, freight = ?, deadline = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (brand, unit_price, quantity, freight, deadline, notes, offer_id),
        )
        self.conn.commit()
        return cur.rowcount > 0

    def count_offers_for_product(self, product_name: str) -> int:
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT COUNT(*) FROM offers o
            JOIN products p ON p.id = o.product_id
            WHERE p.name = ?
            """,
            (product_name,)
        )
        row = cur.fetchone()
        return int(row[0]) if row else 0

    def delete_product(self, product_name: str) -> bool:
        cur = self.conn.cursor()
        cur.execute("SELECT id FROM products WHERE name = ?", (product_name,))
        row = cur.fetchone()
        if not row:
            return False
        pid = int(row[0])
        cur.execute("DELETE FROM products WHERE id = ?", (pid,))
        self.conn.commit()
        return cur.rowcount > 0

    def update_product(self, old_name: str, new_name: str, category: str, quantity: int, unit: str) -> bool:
        cur = self.conn.cursor()
        cur.execute("SELECT id FROM products WHERE name = ?", (old_name,))
        row = cur.fetchone()
        if not row:
            return False
        pid = int(row[0])
        try:
            cur.execute(
                "UPDATE products SET name = ?, category = ?, quantity = ?, unit = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (new_name, category, quantity, unit, pid),
            )
            self.conn.commit()
            return cur.rowcount > 0
        except sqlite3.IntegrityError:
            # name conflict or other integrity issue
            return False

    def _sanitize_filename(self, name: str) -> str:
        if platform.system() == 'Windows':
            invalid = '<>:"/\\|?*'
        else:
            invalid = '/'
        for ch in invalid:
            name = name.replace(ch, '_')
        return ''.join(ch for ch in name if ch.isprintable()).strip().replace(' ', '_')[:60]


def main():
    app = QApplication(sys.argv)
    # Ajuste de escala em Retina
    app.setAttribute(Qt.AA_UseHighDpiPixmaps)
    win = JanelaPrincipal()
    win.show()
    ret = app.exec()
    sys.exit(ret)


if __name__ == "__main__":
    main()


