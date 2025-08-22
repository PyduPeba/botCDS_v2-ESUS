# Arquivo: app/automation/tasks/atend_diabetico_task.py
import asyncio
from playwright.async_api import Locator
from app.automation.tasks.base_task import BaseTask
from app.core.logger import logger
import pandas as pd # Importa pandas para type hinting (opcional)

class AtendimentoDiabeticoTask(BaseTask):
    """
    Tarefa de automação para registrar Atendimento Individual de Diabetes.
    """
    async def _navigate_to_task_area(self) -> Locator:
        """
        Navega até a área de Atendimento Individual no menu principal.
        Implementa o método abstrato da BaseTask.
        """
        logger.info("Navegando para a área de Atendimento Individual (Tarefa Diabético).")
        # Chama o método da classe MainMenu para navegar
        return await self._main_menu.navigate_to_atendimento_individual()
        # navigate_to_atendimento_individual já retorna o FrameLocator do iframe

    async def process_row(self, iframe_frame: Locator, row_data: list):
        """
        Processa uma única linha de dados para registrar um atendimento de Diabetes.
        Implementa o método abstrato da BaseTask.
        Recebe o FrameLocator do iframe e os dados da linha.
        """
        logger.debug(f"Processando linha para Atendimento Diabético: {row_data}")

        # Preenche os campos comuns do paciente (Período, CPF, Data Nasc, Gênero, Local)
        # Usamos a função auxiliar _fill_common_patient_data da BaseTask
        await self._fill_common_patient_data(iframe_frame, row_data)

        # Preenche os campos ESPECÍFICOS da ficha de Atendimento Individual para Diabetes
        # Os dados específicos começam a partir da coluna 5 no seu CSV original
        # (coluna 5: Tipo Atendimento, coluna 6: Condição Avaliada, coluna 7: Conduta)
        # Para Diabético, a Condição Avaliada será "Diabetes" e você mencionou selecionar um exame.
        # O seu código original para Diabético selecionava "S - Hemoglobina glicada" (o 10º checkbox S-...).

        tipo_atendimento = row_data[5] # Ex: "Inicial", "Consulta de Retorno"
        condicao_avaliada_text = "Diabetes" # Texto fixo para esta tarefa
        conduta = row_data[7] # Ex: "Alta de episódio", "Retorno agendado"
        exame_text = "S - Hemoglobina glicada" # Texto fixo ou talvez venha do CSV? Assumindo fixo por enquanto.

        # Chama os métodos da classe AtendimentoForm para preencher estes campos
        await self._atendimento_form.select_tipo_atendimento(iframe_frame, tipo_atendimento)
        await self._atendimento_form.select_condicao_avaliada(iframe_frame, condicao_avaliada_text)
        await self._atendimento_form.select_exame(iframe_frame, exame_text) # Seleciona o exame específico para Diabético
        await self._atendimento_form.select_conduta(iframe_frame, conduta)

        # Clica no botão "Confirmar" da ficha de Atendimento Individual
        # Este método já lida com possíveis alertas (como "Campos duplicados" se aplicável)
        await self._atendimento_form.click_confirm_button(iframe_frame)

        logger.debug("Campos específicos de Atendimento Diabético preenchidos e Confirmar clicado.")

        # Nota: A lógica de clicar em "Adicionar" para a próxima linha está na BaseTask (_process_all_rows).
        # A lógica de salvar/finalizar está em _finalize_task.

    async def _finalize_task(self):
        """
        Finaliza a tarefa clicando no botão "Finalizar Registros".
        Implementa o método abstrato da BaseTask.
        """
        logger.info("Finalizando tarefa de Atendimento Diabético.")
        # Usa o botão "Salvar" do iframe principal
        await self._main_menu.click_finalize_records_button_in_iframe(self._current_iframe_frame)
        await asyncio.sleep(3) # Ajuste conforme necessário