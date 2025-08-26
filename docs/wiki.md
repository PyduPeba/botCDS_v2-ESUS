# 📚 Wiki - botCDS_v2-ESUS

Este projeto é estruturado de forma modular para facilitar a criação de novas tarefas de automação dentro do sistema e-SUS AB (CDS).

## ✅ 1. Criar nova Task

Vá até `app/automation/tasks/` e crie um novo arquivo, como por exemplo:

```python
# app/automation/tasks/proce_hipertensao_task.py
from .base_task import BaseTask

class ProceHipertensaoTask(BaseTask):
    async def run(self, iframe_frame: Locator):
        await self._procedimento_form.fill_sigtap_code(iframe_frame, "XXXX")
```

## ✅ 2. Adicionar lógica de marcação no formulário

Se precisar clicar em novos checkboxes ou campos:

- Vá para `procedimento_form.py`
- Adicione um método como este:

```python
async def marcar_exame_x(self, iframe_frame: Locator):
    await self._safe_click_label(iframe_frame, peid="FichaProcedimentosChildForm.procedimentos", label="Exame X")
```

## ✅ 3. Conecte no `main.py`

Adicione a nova task no `main.py`:

```python
from app.automation.tasks.proce_hipertensao_task import ProceHipertensaoTask

task = ProceHipertensaoTask()
await task.run(iframe_frame)
```

## ✅ 4. Regras gerais

- Evite usar `.nth(0)` sem `has_text()`
- Sempre use `_safe_click`, `_safe_fill_simule` para prevenir falhas
- Use normalização: `.strip().lower()`
- Valide os elementos com `peid` e `label` explícito