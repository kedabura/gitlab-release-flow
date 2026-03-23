# Release
## 🛠 Доступные команды
| Команда | Действие | Описание |
| :--- | :--- | :--- |
| `/get_repo` | **Поиск** | Проекты со слитыми MR за 7 дней. Выбор через чекбоксы. |
| `/get_mr` | **Сбор** | Список всех MR в выбранных репозиториях для проверки. |
| `/mr_prod` | **Ветка** | Создание `master_*` и Merge Request в production. |
| `/create_tag` | **Тег** | Создание финального Git-тега для релиза. |

### ⚙️ Meta (Параметры релиза)

Перед запуском команд убедитесь, что метаданные заполнены корректно:
| Параметр | Формат | Пример значения |
| :--- | :--- | :--- |
| **Release Tag** | `DDMMYY` | `260323` |
| **Approvers** | `user1,user2` | `yusupzhan.ayupov,roman.andreev` |
> ⚠️ **Важно:** В поле `Approvers` логины GitLab указываются через запятую **без пробелов**.

---
## Meta
- Release tag version:
- Approvers: 

## Selected repositories
<!-- automation:repos:start -->
- [ ] loading...
<!-- automation:repos:end -->

## MR
<!-- automation:tasks:start -->
- loading...
<!-- automation:tasks:end -->

## Release preparation
<!-- automation:prepare:start -->
- pending
<!-- automation:prepare:end -->

## Release tags
<!-- automation:tags:start -->
- pending
<!-- automation:tags:end -->