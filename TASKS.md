# Tasks: reorganizar o fluxo de certificados

## Objetivo

Refazer o fluxo para que cada tarefa do Excel seja associada à empresa pelo CNPJ, e só então procurada entre os certificados daquela empresa. Primeiro valide navegação e captura; deixe qualquer edição de certificado para uma etapa posterior.

## 1. `pw/pw_onvio.py`: sessão e navegação geral

- [ ] Manter nesta classe apenas responsabilidades comuns do Onvio: abrir o navegador, criar a sessão, entrar no módulo Processos, navegar até Clientes e encerrar o navegador.
- [ ] Separar a navegação até a tela de pesquisa da ação de abrir uma empresa. `open_emp(cnpj)` deve pesquisar o CNPJ, abrir o resultado correspondente e falhar claramente se não encontrar a empresa.
- [ ] Criar uma forma explícita de voltar à lista de clientes antes de pesquisar outro CNPJ.
- [ ] Garantir que Playwright e navegador sejam inicializados uma única vez. Hoje `PwCert.__init__()` chama `PwOnvio.__init__()`, que inicializa a sessão; depois `OnvioPipe.start_engine()` chama `init_pw()` novamente.
- [ ] Preservar o estado de autenticação ao encerrar a sessão, mas garantir o fechamento do navegador mesmo se uma etapa falhar.

**Aceite:** é possível iniciar o Onvio, abrir uma empresa pelo CNPJ, voltar à pesquisa e abrir outra empresa usando a mesma sessão do navegador.

## 2. `pw/pw_cert.py`: operações na tela de certificados

- [ ] Implementar aqui a ação de abrir a seção **Certificados**, pois ela pertence à interface específica de certificados, não à navegação geral do Onvio.
- [ ] Implementar aqui a captura das atividades exibidas na grade. Retornar dados legíveis para o pipeline, em vez de deixar a extração presa ao script de teste.
- [ ] Implementar aqui a busca de uma atividade na grade já aberta para a empresa atual. Comparar o nome normalizado e clicar somente na linha correspondente quando o chamador pedir uma ação.
- [ ] Separar captura, busca e clique: o teste de captura não deve clicar em uma atividade nem alterar um certificado.
- [ ] Tratar atividade ausente com um resultado explícito, sem clicar em outra linha por aproximação.
- [ ] Ajustar `edit_dates` para receber uma data com um nome de campo consistente com os dados preparados pelo projeto.

**Aceite:** após abrir Certificados para uma empresa, a classe captura apenas as atividades daquela tela; a busca encontra uma atividade pelo nome exato normalizado e não clica quando não há correspondência.

## 3. `pipe/pipeline.py`: orquestração por empresa e tarefa

- [ ] Fazer o pipeline preparar o DataFrame e agrupar os registros por `cnpj`.
- [ ] Para cada CNPJ, abrir a empresa uma vez e pedir a `PwCert` para abrir Certificados e capturar as atividades dessa empresa.
- [ ] Para cada registro do grupo, comparar `registro["tarefa"]` somente com as atividades capturadas para aquele CNPJ.
- [ ] Só depois de confirmar a correspondência, passar o registro completo à operação que atualiza o certificado. Não misturar tarefas de empresas diferentes.
- [ ] Definir o comportamento para atividade não encontrada: registrar empresa, CNPJ e tarefa e seguir para o próximo registro sem editar outra atividade.
- [ ] Corrigir a diferença atual entre a coluna `data` produzida pelo DataFrame e a chave `expiracao` lida por `edit_dates`; escolha um único nome ou faça a conversão explicitamente no pipeline.
- [ ] Garantir que o pipeline não inicialize novamente o Playwright caso a classe de automação já tenha criado a sessão.

**Aceite:** cada atualização usa os dados de uma única linha do DataFrame e só ocorre após confirmar empresa pelo CNPJ e atividade pelo nome.

## 4. `data/prepdf.py`: entrada confiável

- [ ] Manter aqui a leitura e padronização da planilha, incluindo a normalização do CNPJ.
- [ ] Validar a presença das colunas necessárias (`cnpj`, `emp`, `tarefa` e data) e emitir erro claro se a planilha estiver incompleta.
- [ ] Verificar valores vazios de CNPJ, tarefa ou data antes de iniciar a automação.

**Aceite:** o pipeline recebe nomes de colunas previsíveis e não inicia o navegador com registros sem os campos necessários.

## 5. `main/main_teste.py`: validação sem alterações

- [ ] Transformar este arquivo em um teste de diagnóstico do fluxo real: inicializar a sessão, abrir a tela de clientes, pesquisar um CNPJ do DataFrame, entrar na empresa, clicar em Certificados e capturar as atividades.
- [ ] Comparar as atividades capturadas somente com as tarefas do mesmo CNPJ e mostrar `CAPTURADA` ou `NAO ENCONTRADA`.
- [ ] No modo de diagnóstico, não clicar nas linhas de atividade e não chamar `edit_dates`.
- [ ] Mostrar claramente em qual etapa ocorreu uma falha (sessão, pesquisa do CNPJ, abertura da empresa, clique em Certificados ou captura da grade).
- [ ] Depois que o diagnóstico estiver correto, extrair testes unitários para validar comparação de nomes e associação por CNPJ sem depender do site.

**Aceite:** ao executar `python -m main.main_teste`, é possível confirmar visualmente qual empresa foi aberta e quais atividades foram capturadas para ela, sem modificar dados no Onvio.

## Ordem de execução

1. Corrigir ciclo de vida e navegação geral em `PwOnvio`.
2. Implementar abertura de Certificados e captura em `PwCert`.
3. Validar o diagnóstico em uma única empresa e conferir manualmente o CNPJ e os nomes exibidos.
4. Ajustar `OnvioPipe` para percorrer todos os grupos por CNPJ.
5. Resolver a correspondência entre a coluna de data e `edit_dates`.
6. Só habilitar atualizações depois de validar os casos de atividade encontrada, atividade ausente e nomes repetidos.

## Definição de pronto

- [ ] Uma tarefa nunca é comparada com atividades de outro CNPJ.
- [ ] Nenhuma linha é clicada quando o nome não corresponde exatamente após normalização.
- [ ] O diagnóstico pode rodar sem editar certificados.
- [ ] Falhas de navegação ou de dados são reportadas com contexto suficiente para identificar empresa e etapa.
- [ ] O Playwright é iniciado e encerrado uma única vez por execução.