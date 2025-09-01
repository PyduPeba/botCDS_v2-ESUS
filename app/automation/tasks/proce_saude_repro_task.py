# Arquivo: app/automation/tasks/proce_saude_repro_task.py
import asyncio
from playwright.async_api import Locator
from app.automation.tasks.base_task import BaseTask
from app.core.logger import logger
# Não precisamos importar pandas aqui, já importado na BaseTask

class ProcedimentoSaudeReproTask(BaseTask):
    """
    Tarefa de automação para registrar Ficha de Procedimentos de Saúde Sexual e Reprodutiva (Citopatológico).
    """
    async def _navigate_to_task_area(self) -> Locator:
        """
        Navega até a área de Ficha de Procedimentos no menu principal.
        Implementa o método abstrato da BaseTask.
        """
        logger.info("Navegando para a área de Ficha de Procedimentos (Tarefa Saúde Sexual).")
        # Chama o método da classe MainMenu para navegar para Procedimentos
        return await self._main_menu.navigate_to_procedimentos()
        # navigate_to_procedimentos já retorna o FrameLocator do iframe

    async def process_row(self, iframe_frame: Locator, row_data: list):
        """
        Processa uma única linha de dados para registrar um procedimento de Saúde Sexual (Citopatológico).
        Implementa o método abstrato da BaseTask.
        Recebe o FrameLocator do iframe e os dados da linha.
        """
        logger.debug(f"Processando linha para Procedimento Saúde Sexual: {row_data}")

        # Preenche os campos comuns do paciente (Período, CPF, Data Nasc, Gênero, Local)
        # Verifique no seu site real se a ficha de Procedimentos tem esses campos comuns.
        await self._fill_common_patient_data(iframe_frame, row_data)

        await self._procedimento_form.select_exame_do_colo_uterino(iframe_frame)
        await asyncio.sleep(1.5)


        # Clica no botão "Confirmar" da ficha de Procedimentos principal
        # Este método já lida com possíveis alertas (como "Campos duplicados")
        await self._procedimento_form.click_confirm_button(iframe_frame)

        logger.debug("Campos específicos de Procedimento Saúde Sexual preenchidos e Confirmar clicado.")

        # Nota: A lógica de clicar em "Adicionar" para a próxima linha (NOVA FICHA) está na BaseTask (_process_all_rows).
        # Se a lógica for adicionar MULTIPLOS procedimentos DENTRO da mesma ficha,
        # você precisaria ajustar o _process_all_rows na BaseTask ou na tarefa específica.

    async def _finalize_task(self):
        """
        Finaliza a tarefa clicando no botão "Finalizar Registros".
        Implementa o método abstrato da BaseTask.
        """
        logger.info("Finalizando tarefa de Procedimento Saúde Sexual.")
        # Usa o botão "Salvar" do iframe principal
        await self._main_menu.click_finalize_records_button_in_iframe(self._current_iframe_frame)
        # Pode ser necessário adicionar uma espera ou lidar com popup após finalizar.
        await asyncio.sleep(3) # Ajuste conforme necessário

        # Se necessário clicar em "Finalizar registros" para o lote, a lógica deve estar no Worker da GUI.
        # await self._main_menu.click_finalize_records_button_in_iframe(self._current_iframe_frame)
        # await asyncio.sleep(3) # Ajuste conforme necessário