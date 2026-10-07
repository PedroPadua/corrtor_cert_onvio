# Guia de tarefas: automação de certificados Onvio

## Resultado esperado

Para cada registro da planilha, o programa deve:

1. Usar o CNPJ do registro para pesquisar e abrir a empresa.
2. Entrar na seção **Certificados** dessa empresa.
3. Capturar os nomes das atividades exibidas nessa empresa.
4. Comparar a tarefa do registro com esses nomes.
5. Só depois da validação, realizar a ação necessária no certificado.

Até as etapas 1 a 4 estarem testadas, o programa deve apenas navegar, capturar e informar resultados. Não deve clicar em atividades nem salvar alterações no Onvio.

## Como entender `self` e as chamadas

O pipeline guarda um objeto de automação nesta propriedade:

```python
class OnvioPipe:
	def __init__(self):
		self.cert = PwCert()
```

- Dentro de `OnvioPipe`, `self` significa a instância do pipeline. `self.cert` é a instância de `PwCert`.
- Dentro de um método de `PwCert` ou `PwOnvio`, `self` significa essa instância de automação. Como `PwCert` herda de `PwOnvio`, pode chamar os métodos herdados.
- Ao escrever `self.cert.open_emp(cnpj)`, Python passa a instância `self.cert` como o `self` do método automaticamente. Não passe `self` manualmente.
- `page` é um objeto do Playwright. `initial_setup()` já retorna a página `self.proc`; guardar esse retorno permite passá-lo às funções que recebem `page`.

Exemplo de chamadas, depois de implementar os métodos indicados neste guia:

```python
page = self.cert.initial_setup()
page = self.cert.open_emp(cnpj)  # open_emp precisa retornar self.proc
page = self.cert.open_certificates()
atividades = self.cert.capture_activities(page)
encontrada = self.cert.search_certs(page, registro["tarefa"])
```

Não faça `page = self.cert.open_emp(cnpj)` enquanto `open_emp()` não retornar a página. No código atual, esse método não tem `return`, então o valor recebido seria `None`.

## 1. `pw/pw_onvio.py`: sessão e navegação geral

Esta classe controla o navegador e a navegação comum. Ela não deve decidir qual atividade do Excel processar.

- [X] **Inicialização:** garantir que `PwOnvio.__init__()` carregue a configuração e inicialize Playwright, navegador, contexto e página uma única vez. `PwCert.__init__()` chama `super().__init__()`, portanto não chame `init_pw()` de novo no pipeline.
- [X] **Primeira execução:** permitir iniciar sem `pw/onvio_state.json`. Se não houver sessão salva, criar o contexto sem `storage_state`, permitir login e salvar o estado ao encerrar.
- [X] **Acesso à tela de pesquisa:** ajustar `initial_setup()` para chegar à tela em que a caixa “Pesquisar por nome” está disponível. Ela deve retornar a página correta, atualmente `self.proc`.
- [ ] **Abertura da empresa:** em `open_emp(cnpj)`, preencher a pesquisa, localizar o resultado correspondente ao CNPJ, clicar e retornar a página (`return self.proc`). Se não encontrar o resultado, lançar uma exceção válida, por exemplo `raise RuntimeError(...)`. O código atual tenta `raise f'...'`, que não é uma exceção válida.
- [ ] **Volta à lista:** fazer `return_list_emps()` operar na mesma página usada por `open_emp()`. Atualmente o fluxo abre `self.proc`, mas o método volta usando `self.page`; confirme também se “Cancelar” é realmente necessário nessa navegação.
- [ ] **Encerramento:** salvar o estado de autenticação e fechar navegador e Playwright em blocos `finally`, para que uma falha ao salvar ou fechar um recurso não impeça o fechamento dos demais.

**Como testar esta etapa:** abrir uma empresa pelo CNPJ, voltar para a pesquisa e abrir outra. Conferir que a mesma sessão do navegador foi mantida.

**Critério de conclusão:** `initial_setup()` retorna a tela de pesquisa; `open_emp(cnpj)` retorna a página da empresa ou gera erro claro; `return_list_emps()` permite pesquisar o próximo CNPJ; a sessão inicia e encerra uma única vez.

## 2. `pw/pw_cert.py`: tela e atividades de certificados

Esta classe herda a sessão de `PwOnvio` e concentra as ações específicas da seção Certificados.

- [ ] Criar `open_certificates()` para clicar em **Certificados** na empresa que já foi aberta. Retornar a página onde aparece a grade.
- [ ] Criar `capture_activities(page)` para ler os nomes da grade e retornar uma lista, por exemplo `list[str]`. A função não deve clicar nas linhas.
- [ ] Manter a busca de uma tarefa em um método separado. Receber a página e o nome esperado, normalizar maiúsculas e espaços e procurar igualdade exata.
- [ ] Separar “encontrar” de “clicar”: captura e comparação de diagnóstico não alteram a tela. Criar ou chamar uma ação de clique apenas quando o pipeline solicitar explicitamente.
- [ ] Quando não encontrar a atividade, retornar `False` ou resultado equivalente; não clicar em outra linha.
- [ ] Ajustar `edit_dates()` para receber o mesmo campo de data que `prep_df()` entrega. Hoje o DataFrame chama a coluna `data`, mas `edit_dates()` lê `emp_inf['expiracao']`.

**Como testar esta etapa:** abrir uma empresa, clicar em Certificados e imprimir as atividades capturadas. Conferir manualmente alguns nomes. Testar busca com diferença de maiúsculas/espaços e com tarefa inexistente, sem salvar nada.

**Critério de conclusão:** as atividades retornadas pertencem à empresa atualmente aberta; a captura não clica; a busca só considera correspondência exata após normalização.

## 3. `pipe/pipeline.py`: coordenar os passos

O pipeline decide a ordem do trabalho e combina os dados do DataFrame com as operações de `PwOnvio` e `PwCert`. Ele não deve conter seletores CSS nem ler diretamente a grade.

Implemente `pipe()` nesta ordem:

1. Chamar `self.cert.initial_setup()` uma vez e guardar a página retornada.
2. Agrupar `self.df` por `cnpj`, pois várias tarefas podem pertencer à mesma empresa.
3. Para cada grupo, chamar `self.cert.open_emp(cnpj)` uma vez e guardar a página retornada.
4. Chamar `self.cert.open_certificates()` e depois `self.cert.capture_activities(page)` para obter as atividades daquela empresa.
5. Percorrer apenas os registros desse grupo. Comparar cada `registro["tarefa"]` com as atividades capturadas para o CNPJ atual.
6. Se não encontrar, informar empresa, CNPJ e tarefa e continuar para o próximo registro.
7. Durante a fase de diagnóstico, parar após informar a comparação. Só numa fase posterior chamar a ação de clique e `edit_dates()`.
8. Colocar o processamento dentro de `try/finally` e chamar `self.cert.close()` no `finally`.

Modelo de estrutura (os métodos de certificados precisam ser implementados antes):

```python
def pipe(self):
	page = self.cert.initial_setup()
	try:
		for cnpj, registros in self.df.groupby("cnpj", sort=False):
			page = self.cert.open_emp(cnpj)
			page = self.cert.open_certificates()
			atividades = self.cert.capture_activities(page)

			for _, registro in registros.iterrows():
				encontrada = self.cert.search_certs(
					page,
					registro["tarefa"],
				)
				# Nesta fase, apenas registrar o resultado; não editar.
	finally:
		self.cert.close()
```

**Atenção:** o `pipe()` atual percorre linhas sem abrir a empresa pelo CNPJ nem chamar `initial_setup()`. Por isso `self.cert.proc` pode nem existir quando `search_certs()` for chamado.

**Critério de conclusão:** cada comparação acontece dentro do grupo de um único CNPJ, e cada empresa é aberta uma vez por grupo.

## 4. `data/prepdf.py`: preparar os dados

- [ ] Continuar lendo a planilha e renomeando as colunas para `id`, `emp`, `cnpj`, `tarefa` e `data`.
- [ ] Normalizar o CNPJ removendo pontuação e espaços, sem transformar valores ausentes em um CNPJ fictício.
- [ ] Validar se as colunas necessárias existem e informar quais estão faltando.
- [ ] Validar CNPJ, tarefa e data vazios antes de iniciar a automação.

**Como testar esta etapa:** chamar `prep_df()` e conferir `df.columns`, uma amostra de CNPJs normalizados e se existem campos obrigatórios vazios.

## 5. `main/main_teste.py`: diagnóstico sem alterações

- [ ] Usar as classes reais, sem duplicar nelas a lógica de navegação ou captura.
- [ ] Executar o fluxo para um CNPJ de teste: inicializar, pesquisar a empresa, abrir a empresa, clicar em Certificados e capturar as atividades.
- [ ] Comparar somente as tarefas do mesmo CNPJ e mostrar `CAPTURADA` ou `NAO ENCONTRADA`.
- [ ] Não clicar em nenhuma linha de atividade e não chamar `edit_dates()`.
- [ ] Mostrar em qual etapa ocorreu uma falha para facilitar o diagnóstico.

**Como testar esta etapa:** executar `python -m main.main_teste`, conferir visualmente a empresa aberta e comparar os nomes impressos com a tela do Onvio.

## Ordem de trabalho

1. Corrigir `PwOnvio.open_emp()` para retornar a página e lançar exceção válida; corrigir a volta à lista.
2. Garantir que a sessão possa ser criada na primeira execução e encerrada com segurança.
3. Implementar em `PwCert` abrir Certificados e capturar nomes, sem clicar.
4. Fazer o diagnóstico funcionar com um único CNPJ e conferir os nomes na tela.
5. Implementar o agrupamento por CNPJ no pipeline e testar mais de uma empresa.
6. Corrigir o nome/formato da data entre `prep_df()` e `edit_dates()`.
7. Somente depois de validar casos encontrados e não encontrados, habilitar clique e edição.

## Definição de pronto

- [ ] Cada tarefa do Excel é comparada somente com as atividades da empresa daquele CNPJ.
- [ ] Uma atividade não encontrada nunca provoca clique em outra linha.
- [ ] O diagnóstico não modifica certificados.
- [ ] Erros indicam a etapa e o CNPJ envolvidos.
- [ ] Playwright e navegador são inicializados uma única vez e fechados mesmo quando ocorre erro.
