# yatube

Социальная сеть для распространения своих коротких произведений. В ходе проекта было реализовано CRUD приложение, а также настроены статические шаблоны.

## Установка проекта

Как установить проект:

```bash
git clone git@github.com:Anstane/hw05_final.git

cd hw05_final
```
Создаём и активируем виртуальное окружение:
```bash
python -m venv venv

source venv/Scripts/activate
```
Устанавливаем зависимости из файла requirements.txt:
```bash
pip install -r requirements.txt
```
Выполняем миграции:
```bash
python manage.py migrate
```
Активируем сам проект:
```bash
python manage.py runserver
```
