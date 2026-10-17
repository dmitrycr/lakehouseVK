# VK Education — Lakehouse, лабораторная работа №1

**Автор:** Дорогов Дмитрий Алексеевич

**Вариант:** 1 — TPC-H Q3 «Shipping Priority»

Проект реализует локальный Lakehouse для анализа заказов TPC-H. Данные проходят через слои Bronze → Silver → Gold; итоговая витрина содержит десять заказов сегмента `BUILDING` с наибольшей выручкой при заданных ограничениях по датам заказа и отгрузки.

Основные измерения выполнены на `sf5`: 0,866–0,969 ГиБ сжатых файлов на конфигурацию из трёх таблиц. Масштаб выбран с учётом ресурсов локального стенда. Предварительная серия `sf1` и история Iceberg сохранены; объём 50 ГБ в данной работе не достигнут.

Подробные решения, методика и результаты представлены в [отчёте](отчет.md), оформленном по форме лабораторной работы.

## Архитектура

```text
TPC-H → Trino → Bronze → Silver → Gold → Superset
           │
           ├── Lakekeeper REST Catalog → PostgreSQL
           └── Iceberg: файлы данных и метаданных → MinIO S3
```

Bronze сохраняет исходные таблицы `customer`, `orders` и `lineitem`. Silver объединяет данные, применяет фильтры Q3 и рассчитывает выручку позиций. Gold агрегирует выручку по заказам и формирует топ-10. Основные слои используют Iceberg v2, Parquet и ZSTD без партиционирования.

| Компонент | Версия | Назначение |
|---|---|---|
| Trino | 484 | Генерация TPC-H, запись таблиц и аналитические запросы |
| Lakekeeper | 0.14.0 | Каталог Iceberg REST, warehouse `lab` |
| PostgreSQL | 17 | Служебные данные Lakekeeper |
| MinIO | RELEASE.2025-09-07T16-13-09Z, образ dappros/minio | S3-совместимое объектное хранилище |
| Apache Superset | 6.0.0 | SQL Lab и BI через Trino |

## Требования

Для запуска необходимы Docker с Compose и Python 3.9 или новее. Измерения выполнены на Apple M4 с 16 ГиБ RAM; Docker VM предоставляла 10 CPU и около 8 ГиБ RAM.

Перед записью проверяется свободное место: резерв составляет 22 ГиБ плюс оценка предстоящей записи. Полная серия сохраняет 12 копий исходной тройки таблиц, поэтому её суммарный объём существенно больше размера одной конфигурации. Эксперименты следует выполнять последовательно, чтобы избежать конкуренции за ресурсы.

## Подготовка и запуск

Команды выполняются из корня проекта.

```bash
cd lakehouse
# Создание конфигурации только при её отсутствии:
test -f .env || cp .env.example .env
# В .env необходимо задать локальные пароли и ключи из .env.example.
docker compose config --quiet
docker compose up -d
docker compose ps -a
```

В новом окружении после запуска сервисов требуется инициализация warehouse:

```bash
./scripts/init-warehouse.sh
```

Конфигурация основных сервисов находится в [docker-compose.yml](docker-compose.yml), подключение Trino — в [lakehouse.properties](trino/catalog/lakehouse.properties). Пароли и ключи хранятся в `.env`, исключённом из Git. Значение `LAKEKEEPER_PG_ENCRYPTION_KEY` для существующего каталога необходимо сохранять: его изменение требует миграции зашифрованных credentials.

### Исходный конвейер sf1

```bash
docker compose exec -T trino trino --no-progress --execute "$(cat sql/medallion.sql)"
./scripts/verify.sh
```

[medallion.sql](sql/medallion.sql) создаёт отсутствующие таблицы через `IF NOT EXISTS`. Существующие таблицы не перезаписываются; несоответствие данных выявляется проверкой.

Для `sf1` проверяются 150 000 клиентов, 1 500 000 заказов, 6 001 215 позиций Bronze, 30 519 строк Silver и 10 строк Gold. Дополнительно контролируются выручка, NULL, дубликаты и двустороннее совпадение Gold с эталонным Q3 до копеек.

## Результаты sf5

| Слой | Таблица | Строк |
|---|---|---:|
| Bronze | customer | 750 000 |
| Bronze | orders | 7 500 000 |
| Bronze | lineitem | 29 999 795 |
| Silver | q3_order_lines | 150 615 |
| Gold | q3_top_orders | 10 |

Выполнены 36 успешных записей: четыре комбинации формата и кодека, три таблицы и три независимых повтора. Контрольные суммы всех колонок совпали между копиями. Проведены 20 измерений Q3 через `EXPLAIN ANALYZE`; все результаты совпали с исходным запросом. Gold дополнительно проверена двусторонним `EXCEPT`: пропущенных и лишних строк нет.

| Формат | Кодек | Размер Bronze, МБ | Среднее время записи, с | Среднее Execution Q3, мс |
|---|---|---:|---:|---:|
| Parquet | ZSTD | 971,556 | 87,71 | 4972,00 |
| Parquet | GZIP | 930,013 | 110,01 | 4894,00 |
| ORC | ZSTD | 1040,206 | 100,49 | 4384,00 |
| ORC | GZIP | 971,452 | 125,42 | 4518,00 |

МБ = 1 000 000 байт. Размер относится ко всей тройке Bronze и усреднён по трём записям. Время записи измерено вокруг Docker CLI и включает его накладные расходы; Execution — серверное время Trino, усреднённое по пяти прогонам.

Parquet+GZIP обеспечил минимальный размер, Parquet+ZSTD — минимальное среднее время записи. Различия скорости чтения рассматриваются с учётом разброса. Серия выполнялась с перерывом; последняя запись ORC+GZIP повторена после тайм-аута. Частоты CPU и файловый кэш ОС не контролировались. Эти ограничения подробно описаны в отчёте.

Исходные измерения: [запись](results/sf5/writes.csv), [чтение](results/sf5/reads.csv), [контрольные суммы](results/sf5/checksums.csv), [сводка](results/sf5/benchmark_summary.csv), [размеры слоёв](results/sf5/layers.csv), [сверка Gold](results/sf5/gold_comparison.csv).

### Повторное выполнение серии

Для новой серии задаются масштаб и отдельный каталог результатов:

```bash
LAB_SCALE=5 LAB_RESULTS_DIR=results/sf5_new ./scripts/benchmark.sh
LAB_RESULTS_DIR=results/sf5_new python3 scripts/finish-scale.py
LAB_RESULTS_DIR=results/sf5_new python3 scripts/check-scale-bi.py
```

Создаются новые схемы с уникальными суффиксами. Первая Parquet/ZSTD-тройка используется как Bronze для отдельного конвейера Silver/Gold. Скрипт `finish-scale.py` проверяет результаты и формирует SQL и CSV слоёв. `check-scale-bi.py` проверяет чтение через Superset SQL Lab API.

Без параметров `benchmark.sh` использует `sf1`.

SQL завершённой серии: [эталон Q3](sql/q3_reference_sf5.sql), [матрица записей](sql/benchmark_sf5.sql), [Medallion](sql/medallion_sf5.sql), [проверка Gold](sql/verification_sf5.sql). В SQL зафиксированы имена выполненного запуска; для повторной записи с новыми именами используются скрипты выше.

## Superset

```bash
# Необходимы SUPERSET_SECRET_KEY и SUPERSET_ADMIN_PASSWORD в .env.
./scripts/init-superset.sh
```

Инициализация создаёт подключение к Trino, датасет Gold, график и дашборд при их отсутствии. Метаданные Superset хранятся в отдельном volume SQLite; конфигурация рассчитана на локальный учебный стенд.

В [Superset](http://localhost:8088) используется логин `admin` и пароль из `.env`. Подключение: `trino://superset@trino:8080/lakehouse/bronze`. Для `sf5` через SQL Lab проверены группировка клиентов Bronze и чтение десяти заказов Gold. [Протокол API](evidence/logs/superset-sf5-api.txt) и [CSV](results/sf5/superset_bronze.csv) содержат результаты. Существующий [дашборд Q3](http://localhost:8088/superset/dashboard/lakehouse-q3/) относится к `sf1`.

| Сервис | Локальный адрес |
|---|---|
| Trino | [localhost:8080](http://localhost:8080) |
| MinIO Console | [localhost:9001](http://localhost:9001) |
| Lakekeeper | [localhost:8181/ui](http://localhost:8181/ui/) |
| Superset | [localhost:8088](http://localhost:8088) |

Все опубликованные порты привязаны к localhost.

## Дополнительные эксперименты

Schema Evolution, Time Travel, восстановление, компактизация и сравнение настроек кэша выполнены отдельно на `sf1`.

```bash
python3 scripts/lab.py evolution
python3 scripts/metadata.py
python3 scripts/cache.py
python3 scripts/storage_metrics.py
docker compose ps -a
docker system df
df -h .
```

Демонстрации создают новые таблицы. Для сравнения кэша каталоги `cache_on` и `cache_off` указывают на один warehouse с разными значениями `iceberg.metadata-cache.enabled`. После добавления этих конфигураций к существующему контейнеру требуется применить `docker compose up -d --no-deps trino` и дождаться готовности сервиса; команда выполняется после завершения запросов.

Файловый кэш ОС остаётся общим, поэтому повторные запросы не считаются доказательством холодного и тёплого чтения. Размер текущих manifests и data files также не равен полному занятому месту: исторические объекты сохраняются.

## Структура проекта

| Каталог или файл | Содержание |
|---|---|
| [отчет.md](отчет.md) | Отчёт по форме лабораторной работы |
| [sql/](sql/) | Конвейеры, Q3 и проверки |
| [scripts/](scripts/) | Развёртывание, измерения и валидация |
| [results/sf5/](results/sf5/) | Основная серия, размеры слоёв и результаты запросов |
| [results/](results/) | Предварительная серия sf1 и дополнительные эксперименты |
| [evidence/logs/](evidence/logs/) | Выполненные SQL, вывод команд и планы Trino |
| [superset/](superset/) | Образ и конфигурация Superset |
| [trino/catalog/](trino/catalog/) | Конфигурации каталогов Trino |

## Сохранность данных

Данные MinIO, служебное состояние PostgreSQL/Lakekeeper и история Iceberg сохраняются между запусками. Команды `down -v`, очистка томов или бакета, а также удаление снапшотов могут уничтожить данные и доказательства Time Travel; в рабочих сценариях проекта они не используются. `.env`, локальные секреты и файлы дисков исключены из Git.

Описание операций Iceberg и параметров кэширования приведено в [документации Trino](https://trino.io/docs/current/connector/iceberg.html).
