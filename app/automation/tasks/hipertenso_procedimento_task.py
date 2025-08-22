# Arquivo: app/automation/tasks/hipertenso_procedimento_task.py
from playwright.async_api import Locator
from app.automation.tasks.base_task import BaseTask
from app.core.logger import logger
import asyncio # Para await sleep
# Não precisamos importar pandas aqui, já importado na BaseTask

class HipertensoProcedimentoTask(BaseTask):
    """
    Tarefa de automação para registrar Atendimento Individual de Hipertensão
    E Ficha de Procedimentos de Aferição para o mesmo paciente na mesma sessão.
    """
    async def _navigate_to_task_area(self) -> Locator:
        """
        Navega até a área de Atendimento Individual no menu principal,
        pois a automação começa pelo atendimento.
        Implementa o método abstrato da BaseTask.
        """
        logger.info("Navegando para a área de Atendimento Individual (Tarefa Hipertensão/Procedimento).")
        # Chama o método da classe MainMenu para navegar para Atendimento Individual
        return await self._main_menu.navigate_to_atendimento_individual()
        # navigate_to_atendimento_individual já retorna o FrameLocator do iframe

    async def process_row(self, iframe_frame: Locator, row_data: list):
        """
        Processa uma única linha de dados para registrar ATENDIMENTO DE HIPERTENSÃO
        E PROCEDIMENTO DE AFERIÇÃO para o mesmo paciente.
        Implementa o método abstrato da BaseTask.
        Recebe o FrameLocator do iframe e os dados da linha.
        """
        logger.info(f"Processando linha para Hipertenso/Procedimento: {row_data[1]} (CPF/CNS)")

        # -- Passo 1: Registrar Atendimento Hipertenso --

        logger.debug("Preenchendo dados para Atendimento Hipertensão...")
        # Preenche os campos comuns do paciente (Período, CPF, Data Nasc, Gênero, Local)
        await self._fill_common_patient_data(iframe_frame, row_data)

        # Preenche os campos ESPECÍFICOS para Hipertensão (Tipo Atendimento, Condição, Conduta)
        # Assume que as colunas 5, 6, 7 são Tipo Atendimento, Condição Avaliada (Hipertensão), Conduta
        tipo_atendimento = row_data[5]
        condicao_avaliada = row_data[6] # Esperado "Hipertensão"
        conduta = row_data[7]

        await self._atendimento_form.select_tipo_atendimento(iframe_frame, tipo_atendimento)
        await self._atendimento_form.select_condicao_avaliada(iframe_frame, condicao_avaliada)
        await self._atendimento_form.select_conduta(iframe_frame, conduta)

        # Clica no botão "Confirmar" do Atendimento
        await self._atendimento_form.click_confirm_button(iframe_frame)
        logger.debug("Atendimento Hipertensão confirmado para este registro.")

        # -- Passo 2: Adicionar Nova Ficha (Procedimento) para o mesmo paciente --
        # No fluxo "Hipertenso e Procedimento" para o mesmo paciente,
        # após confirmar o Atendimento, você clica em "Adicionar" para adicionar
        # OUTRA ficha (desta vez um procedimento) para o MESMO paciente.
        # Este clique em "Adicionar" NÃO é o que a BaseTask faz automaticamente após processar uma linha,
        # mas sim um clique INTERNO na lógica de processamento desta linha específica.

        await self._main_menu.click_add_button_in_iframe(iframe_frame)
        # Após clicar Adicionar, o formulário de ficha deve aparecer novamente,
        # mas agora você selecionará "Ficha de Procedimentos".

        # -- Passo 3: Selecionar Tipo de Ficha (Procedimento) --
        # Após clicar em Adicionar, o sistema pode te perguntar qual tipo de ficha adicionar.
        # Ou talvez ele já volte para uma tela genérica onde você escolhe.
        # Precisamos de um método na MainMenu ou CommonForms para selecionar "Ficha de Procedimentos".
        # VERIFIQUE COMO O SITE COMPORTA AQUI. Assumindo que aparece uma opção "Ficha de Procedimentos".

        # ESTE SELETOR E MÉTODO SÃO PLACEHOLDERS! VERIFIQUE NO SEU SITE REAL!
        # Talvez seja um botão, um item de menu que aparece, etc.
        # Exemplo: await self._common_forms._safe_click_by_text("Ficha de Procedimentos", "Opção 'Ficha de Procedimentos' após Adicionar")
        # Exemplo 2: Se aparecerem botões para "Nova Ficha de Atendimento Individual" e "Nova Ficha de Procedimentos":
        await self._common_forms._safe_click_by_text("Ficha de Procedimentos", "Opção 'Ficha de Procedimentos' após Adicionar") # Exemplo


        # Agora o formulário DENTRO do iframe mudou para a ficha de Procedimentos para o mesmo paciente.
        # Precisamos preencher os dados do PROCEDIMENTO de Aferição.

        # -- Passo 4: Registrar Procedimento Aferição --
        logger.debug("Preenchendo dados para Procedimento Aferição...")

        # Re-preencher campos comuns? Provavelmente NÃO, o paciente já está selecionado.
        # Mas a DATA DO PROCEDIMENTO pode ser a mesma ou diferente da data do atendimento.
        # Se a data do procedimento for a mesma do atendimento (do data.csv), use self._main_date.
        # Se for outra coluna no seu CSV para a data do procedimento, use row_data[indice_coluna_data_procedimento].
        # Assumindo que é a mesma data principal por enquanto.
        await self._common_forms.fill_date_field(iframe_frame, self._main_date) # Preenche a data na ficha de Procedimento
        # Pode ser necessário selecionar período novamente? Verifique no site. Se sim:
        # await self._common_forms.select_period(iframe_frame, str(row_data[0])) # Período do CSV

        # Preenche os campos ESPECÍFICOS para Procedimento Aferição (SIGTAP)
        sigtap_code = "0301100039" # Código SIGTAP fixo para Aferição

        await self._procedimento_form.fill_sigtap_code(iframe_frame, sigtap_code)

        # Clica no botão "Confirmar" da ficha de Procedimentos
        # Este método já lida com possíveis alertas ("Campos duplicados")
        await self._procedimento_form.click_confirm_button(iframe_frame)
        logger.debug("Procedimento Aferição confirmado para este registro.")

        # NOTA IMPORTANTE: Após processar o Atendimento E o Procedimento para esta linha,
        # A LÓGICA DA BaseTask "_process_all_rows" CLICARÁ AUTOMATICAMENTE no botão "Adicionar"
        # para ir para a PRÓXIMA linha do CSV (NOVO paciente). Isso está correto para esta Task.

    async def _finalize_task(self):
        """
        Finaliza a tarefa clicando no botão "Finalizar Registros".
        Implementa o método abstrato da BaseTask.
        """
        logger.info("Finalizando tarefa de Hipertenso/Procedimento.")
        # Usa o botão "Salvar" do iframe principal
        await self._main_menu.click_finalize_records_button_in_iframe(self._current_iframe_frame)
        # Pode ser necessário adicionar uma espera ou lidar com popup após finalizar.
        await asyncio.sleep(5) # Ajuste conforme necessário, salvar 2 fichas pode demorar

        # Se necessário clicar em "Finalizar registros" para o lote, a lógica deve estar no Worker da GUI.
        # await self._main_menu.click_finalize_records_button_in_iframe(self._current_iframe_frame)
        # await asyncio.sleep(5) # Ajuste conforme necessário
