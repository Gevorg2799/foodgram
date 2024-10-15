# Foodgram

Foodgram - это учебный проект, который представляет из себя сайт, на котором пользователи будут публиковать свои рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Зарегистрированным пользователям также будет доступен сервис «Список покупок». Он позволит создавать список продуктов, которые нужно купить для приготовления выбранных блюд.

---

Проект состоит из следующих страниц:

* главная,
* страница входа,
* страница регистрации,
* страница рецепта,
* страница пользователя,
* страница подписок,
* избранное,
* список покупок,
* создание и редактирование рецепта,
* страница смены пароля.

## Технологии

* Python 3.9
* Django==3.2
* djangorestframework==3.12
* djoser==2.1
* PyJWT==2.9
* pillow==10.4
* gunicorn==20.1
* PostgreSQL ==13

## Документация

### Домен для перехода на действующий проект [https://gevfoodgram.myvnc.com](https://gevfoodgram.myvnc.com)

При локальном запуске приложения, по адресу [http://localhost/api/docs/](http://localhost/api/docs/) будет доступна документация.

Для перехода в админ зону, следует перейти по адресу [http://localhost/admin/](http://localhost/admin/).

Ниже преведены примеры некоторых запросов по api:

* Получить список пользователей(GET-запрос):

  ```
  http://localhost/api/users/
  ```

  ответ будет выглядеть следующим образом:

  ```
  {
    "count": 123,
    "next": "http://foodgram.example.org/api/users/?page=4",
    "previous": "http://foodgram.example.org/api/users/?page=2",
    "results": [
      {
        "email": "user@example.com",
        "id": 0,
        "username": "string",
        "first_name": "Вася",
        "last_name": "Иванов",
        "is_subscribed": false,
        "avatar": "http://foodgram.example.org/media/users/image.png"
      }
    ]
  }
  ```
* Получить список рецептов(GET-запрос):

  ```
  http://localhost/api/recipes/
  ```

  ответ будет выглядеть следующим образом:

  ```
  {
  "count": 123,
  "next": "http://foodgram.example.org/api/recipes/?page=4",
  "previous": "http://foodgram.example.org/api/recipes/?page=2",
  "results": [
      {
      "id": 0,
      "tags": [
          {
          "id": 0,
          "name": "Завтрак",
          "slug": "breakfast"
          }
      ],
      "author": {
          "email": "user@example.com",
          "id": 0,
          "username": "string",
          "first_name": "Вася",
          "last_name": "Иванов",
          "is_subscribed": false,
          "avatar": "http://foodgram.example.org/media/users/image.png"
      },
      "ingredients": [
          {
          "id": 0,
          "name": "Картофель отварной",
          "measurement_unit": "г",
          "amount": 1
          }
      ],
      "is_favorited": true,
      "is_in_shopping_cart": true,
      "name": "string",
      "image": "http://foodgram.example.org/media/recipes/images/image.png",
      "text": "string",
      "cooking_time": 1
      }
  ]
  }
  ```

## Автор:

[**Геворг Хачатрян**](https://github.com/Gevorg2799)
