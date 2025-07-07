# Scripts

В данной директории находятся скрипты, используемые для обработки данных и оценки качества моделей.

## Обзор файлов
```
.
├── data_processing
│   └── process_dataset.py # Скрипт для очистки текстов в датасете с примерами вопросов и ответов
├── evaluation
│   ├── deepeval_evaluate.py # Скрипт для оценки contextual relevancy ответов модели из LangFuse трейсов с использованием DeepEval
│   └── qa_bench.ipynb # Jupyter Notebook для оценки answer relevancy ответов модели ответов модели из LangFuse трейсов с использованием DeepEval
└── README.md
```
