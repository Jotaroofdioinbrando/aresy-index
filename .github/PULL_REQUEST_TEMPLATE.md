## Novo pacote / atualização

**Nome do pacote:**

**O que ele faz (resumo curto):**

---

### Checklist

- [ ] Criei `packages/<nome>/<nome>.ay` com o nome do arquivo idêntico
      ao nome da pasta e à chave que usei no `index.json`
- [ ] Adicionei/atualizei a linha correspondente no `index.json`
- [ ] O arquivo `.ay` **não** define `fn main()`
- [ ] Testei localmente com `aresy install <url-do-meu-fork> <nome>` e
      confirmei que `import <nome>` funciona
- [ ] Não estou sobrescrevendo o pacote de outra pessoa (nome já
      existente com outro dono)

A verificação automática (GitHub Action) confere a parte técnica —
JSON válido, arquivo existe, nomes batendo. A revisão manual é só pra
dar uma olhada geral no código.
