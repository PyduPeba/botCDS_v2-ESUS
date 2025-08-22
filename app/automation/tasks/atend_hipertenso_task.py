# Arquivo: app/automation/tasks/atend_hipertenso_task.py
import asyncio
from playwright.async_api import Locator
from app.automation.tasks.base_task import BaseTask
from app.core.logger import logger
import pandas as pd # Importa pandas para type hinting (opcional)

class AtendimentoHipertensoTask(BaseTask):
    """
    Tarefa de automação para registrar Atendimento Individual de Hipertensão.
    """
    async def _navigate_to_task_area(self) -> Locator:
        """
        Navega até a área de Atendimento Individual no menu principal.
        Implementa o método abstrato da BaseTask.
        """
        logger.info("Navegando para a área de Atendimento Individual (Tarefa Hipertensão).")
        # Chama o método da classe MainMenu para navegar
        return await self._main_menu.navigate_to_atendimento_individual()
        # navigate_to_atendimento_individual já retorna o FrameLocator do iframe

    async def process_row(self, iframe_frame: Locator, row_data: list):
        """
        Processa uma única linha de dados para registrar um atendimento de Hipertensão.
        Implementa o método abstrato da BaseTask.
        Recebe o FrameLocator do iframe e os dados da linha.
        """
        logger.debug(f"Processando linha para Atendimento Hipertensão: {row_data}")

        # Preenche os campos comuns do paciente (Período, CPF, Data Nasc, Gênero, Local)
        # Usamos a função auxiliar que podemos adicionar na BaseTask ou chamar os métodos diretamente
        # Vamos adicionar o método auxiliar na BaseTask para reutilizar
        # Adicione o método _fill_common_patient_data na base_task.py (veja o passo 8, está comentado lá)
        await self._fill_common_patient_data(iframe_frame, row_data)


        # Preenche os campos ESPECÍFICOS da ficha de Atendimento Individual
        # Os dados específicos começam a partir da coluna 5 no seu CSV original
        # (coluna 5: Tipo Atendimento, coluna 6: Condição Avaliada, coluna 7: Conduta)

        tipo_atendimento = row_data[5] # Ex: "Inicial", "Consulta de Retorno"
        condicao_avaliada = row_data[6] # Ex: "Hipertensão"
        conduta = row_data[7] # Ex: "Alta de episódio", "Retorno agendado"
        # O Atendimento Hipertenso no seu código não selecionava Exames nem CIAP, apenas Condição e Conduta.

        # Chama os métodos da classe AtendimentoForm para preencher estes campos
        await self._atendimento_form.select_tipo_atendimento(iframe_frame, tipo_atendimento)
        await self._atendimento_form.select_condicao_avaliada(iframe_frame, condicao_avaliada)
        # O atendimento Hipertenso não tem campo de Exame no seu código original
        await self._atendimento_form.select_conduta(iframe_frame, conduta)

        # Clica no botão "Confirmar" da ficha de Atendimento Individual
        # Este método já lida com possíveis alertas (como "Campos duplicados" se aplicável)
        await self._atendimento_form.click_confirm_button(iframe_frame)

        logger.debug("Campos específicos de Atendimento Hipertensão preenchidos e Confirmar clicado.")

        # Nota: A lógica de clicar em "Adicionar" para a próxima linha está na BaseTask (_process_all_rows).
        # A lógica de salvar/finalizar está em _finalize_task.

    async def _finalize_task(self):
        """
        Finaliza a tarefa clicando no botão "Finalizar registros".
        """
        logger.info("Finalizando tarefa de Atendimento Hipertensão (clicando Finalizar registros).")
        await self._main_menu.click_finalize_records_button_in_iframe(self._current_iframe_frame)   
        await asyncio.sleep(3) # Ajuste conforme necessário
