#!/usr/bin/env python3
from __future__ import annotations

import sys
import csv
import platform
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QSpinBox, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QFileDialog, QMessageBox, QFormLayout, QGroupBox, QStatusBar, QTabWidget
)


@dataclass
class Produto:
    nome: str
    categoria: str
    quantidade: int
    unidade: str


@dataclass
class FornecedorItem:
    fornecedor: str
    marca: str
    preco_unitario: float
    quantidade: int
    frete: float
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

    # ======= Persistência =======
    def mark_dirty(self, dirty: bool = True):
        self.is_dirty = dirty
        title = "Comparação de Preços - Odontopediatria (Qt)"
        if self.current_file:
            title += f" — {self.current_file.name}"
        if self.is_dirty:
            title += " *"
        self.setWindowTitle(title)

    def to_dict(self) -> dict:
        return {
            "produtos": [
                {
                    "nome": p.nome,
                    "categoria": p.categoria,
                    "quantidade": p.quantidade,
                    "unidade": p.unidade,
                }
                for p in self.produtos
            ],
            "fornecedores": {
                nome: [
                    {
                        "fornecedor": it.fornecedor,
                        "marca": it.marca,
                        "preco_unitario": it.preco_unitario,
                        "quantidade": it.quantidade,
                        "frete": it.frete,
                        "prazo": it.prazo,
                        "observacoes": it.observacoes,
                    }
                    for it in itens
                ]
                for nome, itens in self.fornecedores_data.items()
            },
            "version": 1,
        }

    def load_dict(self, data: dict):
        self.produtos.clear()
        self.fornecedores_data.clear()
        for pd in data.get("produtos", []):
            self.produtos.append(Produto(
                nome=pd.get("nome", ""),
                categoria=pd.get("categoria", ""),
                quantidade=int(pd.get("quantidade", 1)),
                unidade=pd.get("unidade", "Unidade"),
            ))
        for nome, itens in data.get("fornecedores", {}).items():
            self.fornecedores_data[nome] = []
            for it in itens:
                self.fornecedores_data[nome].append(FornecedorItem(
                    fornecedor=it.get("fornecedor", ""),
                    marca=it.get("marca", ""),
                    preco_unitario=float(it.get("preco_unitario", 0.0)),
                    quantidade=int(it.get("quantidade", 1)),
                    frete=float(it.get("frete", 0.0)),
                    prazo=it.get("prazo", ""),
                    observacoes=it.get("observacoes", ""),
                ))
        self._refresh_produtos_combo()
        # repopular tabela
        self.table.setRowCount(0)
        for prod in self.produtos:
            for it in self.fornecedores_data.get(prod.nome, []):
                self._append_table_row(prod.nome, it)
        self.mark_dirty(False)

    def file_new(self):
        if not self._maybe_save_changes():
            return
        self.produtos.clear()
        self.fornecedores_data.clear()
        self.table.setRowCount(0)
        self._refresh_produtos_combo()
        self.current_file = None
        self.mark_dirty(False)

    def file_open(self):
        if not self._maybe_save_changes():
            return
        path, _ = QFileDialog.getOpenFileName(self, "Abrir projeto", "", "Projeto (*.json)")
        if not path:
            return
        import json
        try:
            with open(path, "r", encoding="utf-8") as fp:
                data = json.load(fp)
            self.load_dict(data)
            self.current_file = Path(path)
            self.statusBar().showMessage(f"Projeto carregado: {self.current_file}", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao abrir arquivo:\n{e}")

    def file_save_as(self):
        path, _ = QFileDialog.getSaveFileName(self, "Salvar projeto como", "", "Projeto (*.json)")
        if not path:
            return False
        if not path.lower().endswith(".json"):
            path += ".json"
        self.current_file = Path(path)
        return self._write_current_file()

    def file_save(self):
        if not self.current_file:
            return self.file_save_as()
        return self._write_current_file()

    def _write_current_file(self):
        import json
        try:
            with open(self.current_file, "w", encoding="utf-8") as fp:
                json.dump(self.to_dict(), fp, ensure_ascii=False, indent=2)
            self.mark_dirty(False)
            self.statusBar().showMessage(f"Projeto salvo: {self.current_file}", 3000)
            return True
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao salvar arquivo:\n{e}")
            return False

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

        prod = Produto(nome=nome, categoria=cat, quantidade=qtd, unidade=un)
        self.produtos.append(prod)
        self.fornecedores_data[prod.nome] = []
        self._refresh_produtos_combo()
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
        item = FornecedorItem(
            fornecedor=fornecedor,
            marca=marca,
            preco_unitario=preco,
            quantidade=qtd,
            frete=frete,
            prazo=prazo,
            observacoes=obs,
        )
        self.fornecedores_data[produto].append(item)
        # Se o filtro estiver no produto atual, adiciona na tabela
        if self.cmb_filtro_produto.currentText() == produto:
            self._append_table_row(produto, item)

        self.ed_fornecedor.clear()
        self.ed_marca.clear()
        self.ed_preco.clear()
        self.ed_frete.setText("0")
        self.ed_obs.clear()
        self.statusBar().showMessage(f"Fornecedor '{fornecedor}' adicionado para '{produto}'", 3000)
        self.mark_dirty(True)

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
            if c in (3, 5, 6, 7):
                item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(r, c, item)

    def mostrar_melhor_opcao(self):
        # Prioriza a aba de filtro
        produto = self.cmb_filtro_produto.currentText() or self.cmb_produto_sel.currentText()
        if not produto or produto not in self.fornecedores_data:
            QMessageBox.warning(self, "Atenção", "Selecione um produto com fornecedores!")
            return
        itens = self.fornecedores_data[produto]
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
            itens = self.fornecedores_data.get(prod.nome, [])
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
        self.produtos.clear()
        self.fornecedores_data.clear()
        self.table.setRowCount(0)
        self._refresh_produtos_combo()
        self.statusBar().showMessage("Dados limpos", 3000)
        self.current_file = None
        self.mark_dirty(True)

    def _refresh_filtered_table(self):
        self.table.setRowCount(0)
        produto = self.cmb_filtro_produto.currentText()
        if not produto:
            return
        for it in self.fornecedores_data.get(produto, []):
            self._append_table_row(produto, it)

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


