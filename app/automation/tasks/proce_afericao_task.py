# Arquivo: app/automation/tasks/proce_afericao_task.py
import asyncio
from playwright.async_api import Locator
from app.automation.tasks.base_task import BaseTask
from app.core.logger import logger
# Não precisamos importar pandas aqui, já importado na BaseTask

class ProcedimentoAfericaoTask(BaseTask):
    """
    Tarefa de automação para registrar Ficha de Procedimentos de Aferição.
    """
    async def _navigate_to_task_area(self) -> Locator:
        """
        Navega até a área de Ficha de Procedimentos no menu principal.
        Implementa o método abstrato da BaseTask.
        """
        logger.info("Navegando para a área de Ficha de Procedimentos (Tarefa Aferição).")
        # Chama o método da classe MainMenu para navegar para Procedimentos
        return await self._main_menu.navigate_to_procedimentos()
        # navigate_to_procedimentos já retorna o FrameLocator do iframe

    async def process_row(self, iframe_frame: Locator, row_data: list):
        """
        Processa uma única linha de dados para registrar um procedimento de Aferição.
        Implementa o método abstrato da BaseTask.
        Recebe o FrameLocator do iframe e os dados da linha.
        """
        logger.debug(f"Processando linha para Procedimento Aferição: {row_data}")

        # Preenche os campos comuns do paciente (Período, CPF, Data Nasc, Gênero, Local)
        # NOTA: Verifique no seu site real se a ficha de Procedimentos tem EXATAMENTE os mesmos campos comuns
        # que a ficha de Atendimento Individual. Se não, você pode precisar ajustar _fill_common_patient_data
        # ou criar um método similar específico para Procedimentos na BaseTask.
        # Assumindo por enquanto que são os mesmos.
        await self._fill_common_patient_data(iframe_frame, row_data)

        # Preenche os campos ESPECÍFICOS da ficha de Procedimentos para Aferição
        # No seu código original, para aferição, você preenchia o SIGTAP "0301100039".
        # Não há outros campos específicos do CSV para este procedimento no seu código original.

        sigtap_code = "0301100039" # Código SIGTAP fixo para Aferição

        # Chama os métodos da classe ProcedimentoForm para preencher estes campos
        await self._procedimento_form.fill_sigtap_code(iframe_frame, sigtap_code)

        # NOTA: No seu código original, não parecia haver um botão de "Confirmar"
        # para o BLOCO de procedimentos (como o Outros SIA). Apenas o "Confirmar"
        # da ficha principal. Se houver um botão "Adicionar Procedimento" após
        # preencher o SIGTAP e antes de confirmar a ficha, adicione a lógica aqui.
        # Assumindo que após preencher o SIGTAP, você apenas clica no Confirmar da ficha.

        # Clica no botão "Confirmar" da ficha de Procedimentos
        # Este método já lida com possíveis alertas (como "Campos duplicados")
        await self._procedimento_form.click_confirm_button(iframe_frame)

        logger.debug("Campos específicos de Procedimento Aferição preenchidos e Confirmar clicado.")

        # Nota: A lógica de clicar em "Adicionar" para a próxima linha (NOVA FICHA) está na BaseTask (_process_all_rows).
        # Se a lógica for adicionar MULTIPLOS procedimentos DENTRO da mesma ficha
        # antes de confirmar, o clique no "Adicionar" precisa ser movido para DENTRO
        # deste método process_row (e a BaseTask precisaria ser ajustada para não clicar "Adicionar" automaticamente).
        # Assumindo que cada linha do CSV é uma NOVA FICHA de procedimento.

    async def _finalize_task(self):
        """
        Finaliza a tarefa clicando no botão "Finalizar Registros".
        Implementa o método abstrato da BaseTask.
        """
        logger.info("Finalizando tarefa de Procedimento Aferição.")
        # Usa o botão "Salvar" do iframe principal
        await self._main_menu.click_finalize_records_button_in_iframe(self._current_iframe_frame)
        # Pode ser necessário adicionar uma espera ou lidar com popup após finalizar.
        await asyncio.sleep(3) # Ajuste conforme necessário

        # Se necessário clicar em "Finalizar registros" para o lote, a lógica deve estar no Worker da GUI.
        # await self._main_menu.click_finalize_records_button_in_iframe(self._current_iframe_frame)
        # await asyncio.sleep(3) # Ajuste conforme necessário