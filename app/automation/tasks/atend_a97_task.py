# Arquivo: app/automation/tasks/atend_a97_task.py
import asyncio
from playwright.async_api import Locator
from app.automation.tasks.base_task import BaseTask
from app.core.logger import logger
# Não precisamos importar pandas aqui, já importado na BaseTask

class AtendimentoA97Task(BaseTask):
    """
    Tarefa de automação para registrar Atendimento Individual com CIAP A97 (Sem Doença).
    """
    async def _navigate_to_task_area(self) -> Locator:
        """
        Navega até a área de Atendimento Individual no menu principal.
        Implementa o método abstrato da BaseTask.
        """
        logger.info("Navegando para a área de Atendimento Individual (Tarefa A97).")
        # Chama o método da classe MainMenu para navegar
        return await self._main_menu.navigate_to_atendimento_individual()
        # navigate_to_atendimento_individual já retorna o FrameLocator do iframe

    async def process_row(self, iframe_frame: Locator, row_data: list):
        """
        Processa uma única linha de dados para registrar um atendimento A97.
        Implementa o método abstrato da BaseTask.
        Recebe o FrameLocator do iframe e os dados da linha.
        """
        logger.debug(f"Processando linha para Atendimento A97: {row_data}")

        # Preenche os campos comuns do paciente (Período, CPF, Data Nasc, Gênero, Local)
        # Usamos a função auxiliar _fill_common_patient_data da BaseTask
        await self._fill_common_patient_data(iframe_frame, row_data)

        # Preenche os campos ESPECÍFICOS da ficha de Atendimento Individual para A97
        # Os dados específicos começam a partir da coluna 5 no seu CSV original
        # (coluna 5: Tipo Atendimento, coluna 6: Condição Avaliada, coluna 7: Conduta)
        # Para A97, a Condição Avaliada NÃO é selecionada, o CIAP é preenchido com "A97".

        tipo_atendimento = row_data[5] # Ex: "Inicial", "Consulta de Retorno"
        ciap_code = "A97" # Código CIAP fixo para esta tarefa
        conduta = row_data[7] # Ex: "Alta de episódio", "Retorno agendado"
        # Note que a coluna 6 (Condição Avaliada) e Exames NÃO são usados para A97

        # Chama os métodos da classe AtendimentoForm para preencher estes campos
        await self._atendimento_form.select_tipo_atendimento(iframe_frame, tipo_atendimento)
        # Não chama select_condicao_avaliada pois é Sem Doença
        await self._atendimento_form.fill_ciap(iframe_frame, ciap_code) # Preenche o campo CIAP com A97
        # Não chama select_exame
        await self._atendimento_form.select_conduta(iframe_frame, conduta)

        # Clica no botão "Confirmar" da ficha de Atendimento Individual
        # Este método já lida com possíveis alertas (como "Campos duplicados" se aplicável)
        await self._atendimento_form.click_confirm_button(iframe_frame)

        logger.debug("Campos específicos de Atendimento A97 preenchidos e Confirmar clicado.")

        # Nota: A lógica de clicar em "Adicionar" para a próxima linha está na BaseTask (_process_all_rows).
        # A lógica de salvar/finalizar está em _finalize_task.

    async def _finalize_task(self):
        """
        Finaliza a tarefa clicando no botão "Salvar".
        Implementa o método abstrato da BaseTask.
        """
        logger.info("Finalizando tarefa de Atendimento A97.")
        # Usa o botão "Salvar" do iframe principal
        await self._main_menu.click_finalize_records_button_in_iframe(self._current_iframe_frame)
        # Pode ser necessário adicionar uma espera ou lidar com popup após finalizar.
        await asyncio.sleep(3) # Ajuste conforme necessário