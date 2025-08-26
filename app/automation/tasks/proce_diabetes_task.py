# Arquivo: app/automation/tasks/proce_diabetes_task.py
import asyncio
from playwright.async_api import Locator
from app.automation.tasks.base_task import BaseTask
from app.core.logger import logger
import pandas as pd # Importa pandas (opcional, já em BaseTask)

class ProcedimentoDiabeticoTask(BaseTask):
    """
    Tarefa de automação para registrar Ficha de Procedimentos para Diabéticos.
    """
    async def _navigate_to_task_area(self) -> Locator:
        """
        Navega até a área de Ficha de Procedimentos no menu principal.
        Implementa o método abstrato da BaseTask.
        """
        logger.info("Navegando para a área de Ficha de Procedimentos (Tarefa Diabético - Procedimento).")
        # Chama o método da classe MainMenu para navegar para Procedimentos
        return await self._main_menu.navigate_to_procedimentos()
        # navigate_to_procedimentos já retorna o FrameLocator do iframe

    async def process_row(self, iframe_frame: Locator, row_data: list):
        """
        Processa uma única linha de dados para registrar um procedimento para Diabéticos.
        Preenche dois códigos SIGTAP: "0301100039" e "0101040024".
        """
        logger.debug(f"Processando linha para Procedimento Diabético: {row_data}")

        # Preenche os campos comuns do paciente (Período, CPF, Data Nasc, Gênero, Local)
        # Assumimos que são os mesmos campos comuns da ficha de Procedimentos.
        await self._fill_common_patient_data(iframe_frame, row_data)

        # --- ** NOVO PASSO: MARCAR CHECKBOX "Exame do pé diabético" ** ---
        await self._procedimento_form.select_exame_do_pe_diabetico(iframe_frame)
        await asyncio.sleep(2.5) # Pequena pausa após marcar
        

        # --- Interações ESPECÍFICAS PARA PROCEDIMENTO DIABÉTICO (DOIS SIGTAPs) ---
        # ** Preenche o PRIMEIRO Código SIGTAP **
        sigtap_code_1 = "0301100039"
        logger.info(f"Preenchendo PRIMEIRO Código SIGTAP: {sigtap_code_1}")
        await self._procedimento_form.fill_sigtap_code(iframe_frame, sigtap_code_1)
        await asyncio.sleep(0.5) # Pausa após o primeiro SIGTAP ser adicionado


        # ** Preenche o SEGUNDO Código SIGTAP **
        sigtap_code_2 = "0101040024"
        logger.info(f"Preenchendo SEGUNDO Código SIGTAP: {sigtap_code_2}")
        await self._procedimento_form.fill_sigtap_code(iframe_frame, sigtap_code_2)
        await asyncio.sleep(0.5) # Pausa após o segundo SIGTAP ser adicionado


        # --- Clica no botão "Confirmar" da ficha de Procedimentos (APÓS AMBOS OS SIGTAPS) ---
        await self._procedimento_form.click_confirm_button(iframe_frame)
        logger.debug("Campos específicos de Procedimento Diabético (dois SIGTAP) preenchidos e Confirmar clicado.")

    async def _finalize_task(self):
        """
        Finaliza a tarefa clicando no botão "Finalizar Registros".
        Implementa o método abstrato da BaseTask.
        """
        logger.info("Finalizando tarefa de Procedimento Diabético.")
        # Usa o botão "Finalizar registros" do iframe principal
        await self._main_menu.click_finalize_records_button_in_iframe(self._current_iframe_frame)
        await asyncio.sleep(3) # Ajuste conforme necessário