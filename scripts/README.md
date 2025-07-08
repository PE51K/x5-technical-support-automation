# Scripts

В данной директории находятся скрипты, используемые для обработки данных и оценки качества моделей.

## Обзор файлов
```
.
├── data_processing
│   ├── process_data.py # Скрипт для очистки текстов в датасете с примерами вопросов и ответов (тестовый вариант)
│   └── process_data_final.py # Скрипт для очистки текстов в датасете с примерами вопросов и ответов (финальный вариант)
├── evaluation
│   ├── deepeval_answer_relevancy.ipynb # Jupyter Notebook для оценки answer relevancy ответов модели из LangFuse трейсов с использованием DeepEval
│   └── deepeval_contextual_relevancy.py # Скрипт для оценки contextual relevancy ответов модели из LangFuse трейсов с использованием DeepEval
├── README.md
└── training
    └── train_retrieval.ipynb # Jupyter Notebook для обучения эмбеддера на triplet loss
```
