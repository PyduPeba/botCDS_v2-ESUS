# File: app/automation/tasks/atend_saude_repro_task.py
import asyncio
from playwright.async_api import Locator
from app.automation.tasks.base_task import BaseTask
from app.core.logger import logger
# No need to import pandas here, already imported in BaseTask

class AtendimentoSaudeReproTask(BaseTask):
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

        tipo_atendimento = row_data[5]
        condicao_avaliada_text = "Saúde sexual e reprodutiva" # Fixed text for this task
        conduta = row_data[7]
        # The original code also filled a SIGTAP-like field (0203010019) here, which
        # typically belongs to a PROCEDURE. We will replicate this by calling
        # the appropriate method from ProcedimentoForm if it's the same field.
        # Assuming the field "Exame" in the "Outros SIA" block (used in Procedures)
        # is also present and fillable in the ATTENDANCE form for this specific condition.
        # This is unusual and needs verification on the real site.
        exame_sia_code_or_text = "0203010019" # Code or text for Citopatológico
        status_sia = "S" # Status fixed for the SIA block


        # Call methods from the AtendimentoForm class for Attendance fields
        await self._atendimento_form.select_tipo_atendimento(iframe_frame, tipo_atendimento)
        # Select the specific condition using the text
        await self._atendimento_form.select_condicao_avaliada(iframe_frame, condicao_avaliada_text)
        # Call the method to fill the Outros SIA field, even in Attendance (replicate original logic)
        # We need a method in AtendimentoForm or BasePage if this field exists *only* when this condition is selected.
        # Or, if it's the SAME field as in ProcedimentoForm's Outros SIA block,
        # we could potentially call a method from ProcedimentoForm here, but that couples tasks to other forms.
        # A better approach: Add a method to AtendimentoForm to handle this specific SIA field if it appears here.
        # Let's assume AtendimentoForm has a method for this if it's a field within the Attendance form.
        # If it's the *exact* same block as in Procedures, maybe ProcedimentoForm methods are fine, but odd structure.
        # Let's create a method in AtendimentoForm to handle this if necessary, or reuse if possible.
        # For now, assuming the field is part of the AtendimentoForm when this condition is selected.

        # Looking back at `sigtap_citopatologico_cervico` in digita_sigtap.py, it uses PEID 'OutrosSiaForm.siaSelectDto'
        # and 'OutrosSiaForm.status' and 'OutrosSiaAtendimentoIndividualComponentFlexList.Confirmar'.
        # These PEIDs suggest it's the SAME block as in ProcedimentoForm. This is odd.
        # This implies the "Outros SIA" block is sometimes included in the Attendance form UI.
        # The cleanest way is to put methods for this specific block in ProcedimentoForm,
        # and call them FROM the AttendanceTask if the UI includes that block.
        # This couples the task to *both* form types, but reflects the unusual UI.

        # Let's call the methods from ProcedimentoForm, but pass the iframe_frame from Attendance
        await self._procedimento_form.fill_outros_sia_exame(iframe_frame, exame_sia_code_or_text)
        await self._procedimento_form.select_outros_sia_status(iframe_frame, status_sia)
        await self._procedimento_form.click_outros_sia_confirm_button(iframe_frame)
        await asyncio.sleep(1) # Pause after confirming SIA block

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