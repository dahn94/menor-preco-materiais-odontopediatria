Nota rápida: removendo `.venv` do staging do Git

Se você acidentalmente adicionou a pasta `.venv` com `git add .`, remova-a do staging com:

```bash
git restore --staged .venv
# ou, em versões antigas do git:
git reset HEAD .venv
```

Em seguida, adicione `.venv/` ao arquivo `.gitignore` para evitar que seja rastreada:

```text
.venv/
```

Commit e continue normalmente.

Novas funcionalidades (editar/deletar ofertas)

Adicionamos controles na aba "Filtro": você pode selecionar uma linha da tabela e usar os botões "Editar Selecionado" e "Deletar Selecionado" para gerenciar as ofertas existentes. O diálogo de edição permite alterar marca, preço unitário, quantidade, frete, prazo e observações.

Se quiser eu atualizo o `README.md` principal com essa nota (ou faço um PR com a mudança).