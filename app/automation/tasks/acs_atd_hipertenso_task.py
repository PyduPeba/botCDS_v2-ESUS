# Arquivo: app/automation/tasks/acs_atd_hipertenso_task.py (VERSÃO v2b - Selecionando Checkboxes)
from playwright.async_api import Locator
from app.automation.tasks.base_task import BaseTask
from app.core.logger import logger
import asyncio

class AcsAtdHipertensoTask(BaseTask):
    """
    Tarefa para o ACS registrar Atendimento de Hipertensão em Visita Domiciliar.
    Agora segue o padrão de herança da BaseTask, sem duplicar o método 'run'.
    """

    async def _perform_pre_navigation_steps(self):
        """
        Sobrescreve o gancho da BaseTask para executar a seleção de perfil
        específica para o ACS.
        """
        logger.info("Executando passo de pré-navegação: Seleção de perfil do ACS.")
        profile_selected = await self._login_page.select_profile_and_unidade_optional(
            profile_name_to_select="AGENTE COMUNITARIO DE SAUDE"
        )
        if not profile_selected:
            logger.warning("Não foi possível selecionar o perfil do ACS. A automação continuará com o perfil padrão.")
        else:
            logger.info("Perfil do ACS selecionado com sucesso.")

    async def _navigate_to_task_area(self) -> Locator:
        """
        Implementa o método abstrato para navegar até a área de
        Visita Domiciliar e Territorial.
        """
        logger.info("Navegando para a área de Visita Domiciliar do ACS.")
        return await self._main_menu.navigate_to_acs_visita_domiciliar()

    async def process_row(self, iframe_frame: Locator, row_data: list):
        """
        Processa uma única linha de dados.
        NOTA: Atualmente, reutiliza a lógica de preenchimento do atendimento de hipertensão.
        Isso deve ser adaptado quando os campos da ficha de Visita Domiciliar forem mapeados.
        """
        logger.debug(f"Processando linha para Visita Domiciliar (Hipertensão): {row_data}")

        # 1. Preenche dados comuns do paciente
        await self._fill_common_patient_acs(iframe_frame, row_data)

        # 2. Preenche campos específicos do formulário
        # ATENÇÃO: A ficha de Visita Domiciliar pode ter campos diferentes.
        await self._acs_form.select_motivo_visita_periodica(iframe_frame)
        await self._acs_form.select_acompanhamento_hipertensao(iframe_frame)
        await self._acs_form.select_desfecho_visita_realizada(iframe_frame)

        # 3. Confirma o registro do paciente
        # A ficha de Visita pode ter um botão de confirmar diferente. Usando o de Atendimento por enquanto.
        await self._acs_form.click_confirm_button_acs(iframe_frame)

        logger.debug("Linha da Visita Domiciliar processada e confirmada.")

    async def _finalize_task(self):
        """
        Finaliza o lote de registros para a ficha de Visita Domiciliar.
        """
        logger.info("Finalizando tarefa de Visita Domiciliar (clicando em 'Finalizar registros').")
        await self._main_menu.click_finalize_records_button_in_iframe(self._current_iframe_frame)
        await asyncio.sleep(3)