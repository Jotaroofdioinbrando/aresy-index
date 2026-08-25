# Como publicar uma biblioteca no aresy-index

Este repositório é o "PyPI" do aresY: um lugar só onde ficam todas as
bibliotecas da comunidade. Publicar uma é só um Pull Request — não
precisa criar repositório nenhum.

## Passo a passo

1. **Faça um fork** deste repositório e clone o seu fork.

2. **Crie a pasta da sua lib** dentro de `packages/`, com um arquivo
   `.ay` cujo nome bate exatamente com o nome do pacote:

   ```
   packages/
     minhalib/
       minhalib.ay
   ```

   Regras importantes:
   - O nome do arquivo (sem `.ay`) precisa ser **idêntico** ao nome da
     pasta e ao nome que vai usar no `index.json` — maiúsculas/minúsculas
     incluídas (`numAres` ≠ `numares`).
   - Por enquanto, cada pacote é **um único arquivo `.ay`**. Se sua lib
     precisa de mais de um arquivo, use `import "outroarquivo.ay"` dentro
     do seu `.ay` principal apontando pra um arquivo na mesma pasta.
   - Não defina `fn main()` no arquivo da lib — bibliotecas não têm
     ponto de entrada próprio, só declaram funções pra quem importar.

3. **Adicione uma linha no `index.json`** da raiz, com o nome do pacote
   apontando pro caminho do arquivo:

   ```json
   {
     "minhalib": "packages/minhalib/minhalib.ay"
   }
   ```

   Mantenha a ordem alfabética das chaves, se der — ajuda quem for
   revisar.

4. **Abra o Pull Request.** Uma Action automática já confere:
   - se o `index.json` continua um JSON válido,
   - se o arquivo que você referenciou existe,
   - se o nome do arquivo bate com a chave do `index.json`,
   - se você não está sobrescrevendo sem querer o pacote de outra
     pessoa que já existia.

   Se a Action passar (✅ verde), é só esperar a revisão manual.

## O que evitar

- Não sobrescreva um pacote que não é seu (se colidir com o nome de
  outra lib já publicada, escolha outro nome).
- Não suba código malicioso ou que rode comandos do sistema sem avisar
  claramente no nome/descrição do pacote.
- Prefira nomes descritivos e em minúsculas/camelCase simples — evite
  nomes genéricos demais tipo `utils` ou `lib`.

## Testando localmente antes de abrir o PR

No seu projeto aresY, aponte a instalação direto pro seu fork (sem
precisar mesclar nada ainda):

```
aresy install https://raw.githubusercontent.com/<seu-usuario>/aresy-index/<sua-branch>/packages/minhalib/minhalib.ay minhalib
```

Se o programa que usa `import minhalib` compilar e rodar certo, seu
pacote está pronto pro PR.
