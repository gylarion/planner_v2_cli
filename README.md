# UA
# Planner V2 CLI

## Опис проєкту

Planner V2 CLI — це консольний застосунок для планування задач, створений як
демонстраційна версія (proof of concept) більшого багатокористувацького планувальника.

Проєкт зосереджений на архітектурі, доменній логіці та правилах доступу, а не на
користувацькому інтерфейсі. Поточна реалізація у вигляді CLI дозволяє перевірити
основні ідеї, моделі та бізнес-правила системи без використання веб-фреймворків
та фронтенду.

---

## Ідея та первинне бачення проєкту

Первинна ідея проєкту полягала у створенні веб-застосунку — спільного планувальника
задач для невеликих груп людей: сім’ї, друзів або близького кола.

За задумом, система мала виконувати роль своєрідного “месенджера задач”, де
користувачі могли б:
- створювати та призначати задачі один одному,
- встановлювати відкладені нагадування на певний час,
- координувати побутові або групові справи асинхронно,
- уникати ситуацій, коли важливі прохання або нагадування губляться.

Приклади реальних сценаріїв використання:
- нагадати члену родини зайти до магазину та придбати необхідні товари,
- поставити відкладене нагадування, якщо людина зараз зайнята,
- вести спільний список домашніх або групових задач без необхідності постійного листування.

Поточна CLI-версія не реалізує повний функціонал цієї ідеї, але слугує
архітектурним прототипом, який демонструє, як така система може бути
спроєктована та розширена у майбутньому у вигляді повноцінного веб-застосунку.

---

## Поточний стан проєкту

Цей проєкт є демонстраційним та **не доведений до завершеного продукту**.

Поточна реалізація:
- є CLI-застосунком,
- не містить веб-інтерфейсу,
- не реалізує реальні нагадування або фонові задачі,
- не призначена для використання у продакшені.

CLI-версія створена з метою демонстрації архітектурних рішень, доменної логіки
та системи доступу, а не як готовий користувацький продукт.

---

## Реалізований функціонал

На поточний момент реалізовано:

- створення користувачів (users) та гостьових сесій (guests),
- авторизація користувачів та гостей у CLI,
- створення планерів з різними режимами доступу,
- підтримка ролей: OWNER, ADMIN, MEMBER,
- система прав доступу до задач та дій,
- створення, редагування та видалення задач,
- система запрошень (invites) для приєднання до планера,
- гостьові планери з автоматичним терміном дії,
- журнал дій (logs),
- збереження стану застосунку у JSON-файл,
- інтерактивний CLI з контекстним prompt та історією команд.

---

## Архітектура та структура проєкту

Проєкт побудований з чітким розділенням відповідальностей:

- **models** — доменні моделі (dataclasses),
- **services** — бізнес-логіка та правила роботи з доменом,
- **access layer** — перевірка прав та ролей користувачів,
- **cli** — обробка команд, контекст користувача та взаємодія через консоль,
- **storage** — збереження та завантаження стану застосунку у JSON-форматі.

Сервісний шар не залежить від способу збереження даних або інтерфейсу користувача,
що дозволяє у майбутньому замінити CLI на веб-інтерфейс без переписування бізнес-логіки.

---

## Архітектурні рішення

У процесі розробки були прийняті такі рішення:

- CLI використовується як простий спосіб демонстрації логіки системи.
- Дані зберігаються у JSON-файлі для прозорості та простоти демо.
- Користувачі та гості є різними сутностями з різними правилами.
- Ідентифікація сутностей відбувається за унікальними ID, а не за назвами.
- Бізнес-логіка ізольована від шару збереження та інтерфейсу.

---

## Відомі обмеження

На поточний момент відомі наступні обмеження:

- система нагадувань та сповіщень не реалізована,
- механізм подачі та підтвердження запитів на доступ реалізований на рівні сервісів,
  але не виведений у CLI,
- відсутній веб-інтерфейс,
- відсутні автоматизовані тести,
- CLI орієнтований на демонстрацію, а не на кінцевого користувача.

---

## Як запустити проєкт

```bash
python main.py
```

#  ENG
# Planner V2 CLI

## Project Overview (Introduction)

Planner V2 CLI is a command-line task planning application created as a
**proof of concept** for a larger multi-user planner system.

The project focuses on architecture, domain logic, and access control rules
rather than on user interface design. The current CLI implementation allows
core ideas, models, and business rules to be validated without relying on
web frameworks or frontend technologies.

---

## Project Vision

The original idea behind the project was to build a web-based application —
a shared task planner for small private groups such as families, couples,
or close friends.

The system was envisioned as a kind of “task messenger”, where users could:
- create and assign tasks to each other,
- schedule delayed reminders for a specific time,
- coordinate household or group responsibilities asynchronously,
- avoid situations where important requests or reminders are forgotten.

Example real-life use cases include:
- reminding a family member to stop by a store and buy necessary items,
- setting delayed reminders when someone is currently busy,
- maintaining a shared list of household or group tasks without constant messaging.

The current CLI version does not implement the full scope of this idea, but
serves as an architectural prototype that demonstrates how such a system
could be designed and later expanded into a full-featured web application.

---

## Project Status

This project is **demonstrational and incomplete by design**.

The current implementation:
- is a CLI-based application,
- does not include a web interface,
- does not implement real-time notifications or background schedulers,
- is not intended for production use.

The CLI version was built to demonstrate architectural decisions, domain
modeling, and access control logic rather than to function as a finished product.

---

## Implemented Features

At the current stage, the following functionality is implemented:

- user and guest session creation,
- user and guest authentication within the CLI,
- planner creation with different access modes,
- role support: OWNER, ADMIN, MEMBER,
- role-based access control and permissions,
- task creation, editing, and deletion,
- invite-based access to planners,
- guest planners with automatic expiration,
- action logging (audit trail),
- persistent JSON-based storage,
- interactive CLI with contextual prompt and command history.

---

## Architecture

The project is built with a clear separation of responsibilities:

- **models** — domain models implemented as dataclasses,
- **services** — business logic and domain rules,
- **access layer** — role and permission checks,
- **cli** — command handling, user context, and console interaction,
- **storage** — loading and saving application state using JSON.

The service layer is independent of both the storage mechanism and the user
interface, allowing the CLI to be replaced by a web interface in the future
without rewriting core business logic.

---

## Design Decisions

The following design decisions were made during development:

- A CLI was chosen as a simple and transparent way to demonstrate system logic.
- JSON-based storage was used for persistence to keep the demo lightweight and readable.
- Users and guests are modeled as separate entities with different rules.
- System entities are identified by unique IDs rather than by human-readable names.
- Business logic is isolated from both the storage layer and the user interface.

These decisions provide a solid foundation for future expansion into a
full-featured web application.

---

## Known Limitations

The following limitations are currently known and documented:

- reminder scheduling and notification delivery are not implemented,
- access request approval and rejection are implemented at the service level
  but are not exposed via CLI commands,
- no web interface is provided,
- automated tests are not included,
- the CLI is focused on architectural demonstration rather than end-user UX.

---

## How to Run

```bash
python main.py
