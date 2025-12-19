# File: app/automation/tasks/atend_saude_mamografia_task.py 
import asyncio
from playwright.async_api import Locator
from app.automation.tasks.base_task import BaseTask
from app.core.logger import logger
# No need to import pandas here, already imported in BaseTask

class AtendimentoMamografiaTask(BaseTask):
    """
    Automation task to register Individual Attendance for Reproductive Health.
    Includes selecting the condition and potentially filling an Outros SIA field.
    """
    async def _navigate_to_task_area(self) -> Locator:
        """
        Navigates to the Individual Attendance area from the main menu.
        Implements the abstract method from BaseTask.
        """
        logger.info("Navigating to the Individual Attendance area (Reproductive Health Task).")
        # Call the method from the MainMenu class to navigate
        return await self._main_menu.navigate_to_atendimento_individual()
        # navigate_to_atendimento_individual already returns the FrameLocator of the iframe

    async def process_row(self, iframe_frame: Locator, row_data: list):
        """
        Processes a single data row to register a Reproductive Health attendance.
        Implements the abstract method from BaseTask.
        Receives the FrameLocator of the iframe and the row data.
        """
        logger.debug(f"Processing row for Reproductive Health Attendance: {row_data}")

        # Fill common patient fields (Period, CPF, DOB, Gender, Location)
        # Use the helper function _fill_common_patient_data from BaseTask
        await self._fill_common_patient_data(iframe_frame, row_data)

        # Fill SPECIFIC fields for the Individual Attendance form
        # Based on your original code:
        # Column 5: Tipo Atendimento
        # Column 6: Condição Avaliada (Expected "Saúde sexual e reprodutiva")
        # Column 7: Conduta
        # Also used sigtap_citopatologico_cervico which fills an Outros SIA field

        tipo_atendimento = "Consulta agendada"
        condicao_avaliada_text = "Saúde sexual e reprodutiva" # Fixed text for this task
        # rastreamento_label = "Câncer de mama"
        rastreamento_label = "Câncer do colo do útero" # Overwrite to use Cervical Cancer as per original code
        conduta = row_data[7]
        
        # exame_sia_code = "0204030188" # Code or text for Citopatológico
        exame_sia_code = "0203010086" # EXAME CITOPATOLÓGICO CERVICO VAGINAL/MICROFLORA-RASTREAMENTO
        status_sia = "S" # Status fixed for the SIA block


        # Call methods from the AtendimentoForm class for Attendance fields
        await self._atendimento_form.select_tipo_atendimento_fixo(iframe_frame, tipo_atendimento)
        # Select the specific condition using the text
        await self._atendimento_form.select_condicao_avaliada(iframe_frame, condicao_avaliada_text)
        await asyncio.sleep(0.5) # Small pause to ensure dropdown is ready
        logger.debug(f"Selecting specific condition: {rastreamento_label}")
        await self._atendimento_form.select_condicao_avaliada(iframe_frame, rastreamento_label)


        # --- ALTERAÇÃO PRINCIPAL: Chamando a nova função centralizada ---
        # A função abaixo agora cuida de digitar, selecionar, marcar 'S' e confirmar o bloco.
        await self._atendimento_form.fill_outros_exames_sigtap(iframe_frame, exame_sia_code)
        await asyncio.sleep(1) # Pausa após confirmar o bloco
        # --- FIM DA ALTERAÇÃO ---

        # Select the Conduta
        await self._atendimento_form.select_conduta(iframe_frame, conduta)

        # Clica no botão "Confirmar" da ficha de Atendimento Individual
        await self._atendimento_form.click_confirm_button(iframe_frame)

        logger.debug("Campos específicos de Atendimento Saúde Sexual preenchidos e Confirmar clicado.")

        # Note: The logic for clicking "Adicionar" for the next row is in the BaseTask (_process_all_rows).
        # The logic for saving/finalizing is in _finalize_task.


    async def _finalize_task(self):
        """
        Finalizes the task by clicking the "Finalizar Registros" button.
        Implements the abstract method from BaseTask.
        """
        logger.info("Finalizing Reproductive Health Attendance task.")
        # Use the "Salvar" button from the main iframe
        await self._main_menu.click_finalize_records_button_in_iframe(self._current_iframe_frame)
        # Pode ser necessário adicionar uma espera ou lidar com popup após finalizar.
        await asyncio.sleep(3) # Adjust as needed

        # Finalize records logic (for the batch) should be in the GUI Worker.
        # await self._main_menu.click_finalize_records_button_in_iframe(self._current_iframe_frame)
        # await asyncio.sleep(3) # Adjust as needed