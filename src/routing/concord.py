import json

from fastapi import APIRouter, Request, Form
from config import logger, templates, settings, session_manager
from repositories.logics import get_bitrix_auth


app_concord = APIRouter()


@app_concord.post("/task_panel/", tags=['CONCORDING'], summary="Панель согласования для задач")
@logger.catch
async def task_panel(
        request: Request,
        AUTH_ID: str = Form(),
        PLACEMENT_OPTIONS: str = Form(),

):
    # return templates.TemplateResponse(request, name="install.html")
    """Панель для согласования договора в задаче"""
    session = await session_manager.get_session()

    placement_options = json.loads(PLACEMENT_OPTIONS)

    user = await session.post(
        url=f"{settings.portal_url}rest/user.current",
        params={
            'auth': AUTH_ID
        }
    )
    user_admin = await session.post(
        url=f"{settings.portal_url}rest/user.admin",
        params={
            'auth': AUTH_ID
        }
    )

    access = await get_bitrix_auth()
    # получить привязанные элементы tasks.task.get | taskId=441215&select[0]=UF_CRM_TASK
    task = await session.post(
        url=f"{settings.portal_url}rest/tasks.task.get.json/",
        json={
            'auth': access[0],
            'taskId': placement_options['taskId'],
            'select': ['ACCOMPLICES', 'RESPONSIBLE_ID', 'UF_CRM_TASK', 'TITLE'],
        }
    )
    task = await task.json()
    if 'ufCrmTask' not in task['result']['task']:
        return "Нет привязки элемента к CRM"
    if not task['result']['task']['ufCrmTask']:
        return "Нет привязки элемента к CRM"
    if task['result']['task']['ufCrmTask'][0][:4] != 'T83_':
        return "Нет привязки к процессу согласования договора"
    element_id = task['result']['task']['ufCrmTask'][0][4:]
    element = await session.post(
        url=f"{settings.portal_url}rest/crm.item.get.json",
        json={
            'auth': access[0],
            'entityTypeId': 131,
            'id': element_id,
            'select': [
                'ufCrm12_1709191865371',
                'ufCrm12_1709192259979',
                'ufCrm12_1708599567866',
                'ufCrm12_1708093511140',
                'CREATED_BY',
            ],
        }
    )
    accomplices = task['result']['task']['accomplices'][0]
    accountants = await session.post(
        url=f"{settings.portal_url}rest/user.search.json",
        json={
            'auth': access[0],
            'UF_DEPARTMENT': 114
        }
    )
    accountants = await accountants.json()
    list_accountants = []
    for i in accountants["result"]:
        list_accountants.append(i["ID"])
    for a in task['result']['task']['accomplices']:
        if a in list_accountants:
            accomplices = a
    element = await element.json()
    user = await user.json()
    user_admin = await user_admin.json()
    list_access = {
        '114': 'accountant',
        '94': 'lawyer',
        '0': 'admin'
    }  # бухгалтера, юристы
    if element['result']["item"]['ufCrm12_1712146917716']:
        attached_file = True
    else:
        attached_file = False
    approval_status = {
        "accountant": element['result']["item"]['ufCrm12_1709191865371'],
        "lawyer": element['result']["item"]['ufCrm12_1709192259979']
    }
    for i in user['result']['UF_DEPARTMENT']:  # перебираем все подразделения сотрудника
        if str(i) in list_access or user_admin['result']:  # Если есть разрешение
            if user_admin['result']:
                i = '0'
            return templates.TemplateResponse(
                request,
                name="task_panel.html",
                context={
                    'element_id': element_id,
                    'task_id': placement_options['taskId'],
                    'user_id': user['result']['ID'],
                    'access': list_access[str(i)],
                    'approval_status': approval_status,
                    'attached_file': attached_file,
                    'accomplices': accomplices,
                    'responsible': task['result']['task']['responsibleId'],
                    'title_task': task['result']['task']['title'],
                    'auth': access[0],
                    'comment_accountant':
                        element['result']["item"]['ufCrm12_1708599567866'],
                    'created_by': element['result']["item"]['createdBy'],
                    'portal_url': settings.portal_url,
                    'hosting_url': settings.hosting_url
                }
            )
    return "Доступ запрещен"
