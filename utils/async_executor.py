"""
Утилита для выполнения функций в отдельных потоках
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, List, Any, Dict
import threading


class AsyncExecutor:
    """Executor для параллельного выполнения задач"""

    def __init__(self, max_workers: int = 5):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self._lock = threading.Lock()

    def submit(self, func: Callable, *args, **kwargs):
        """Отправить задачу на выполнение"""
        return self.executor.submit(func, *args, **kwargs)

    def map_parallel(self, func: Callable, items: List[Any]) -> List[Any]:
        """
        Выполнить функцию параллельно для списка элементов

        Args:
            func: Функция для выполнения
            items: Список элементов

        Returns:
            Список результатов
        """
        futures = [self.executor.submit(func, item) for item in items]
        results = []
        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception:
                results.append(None)
        return results

    def run_parallel(self, tasks: Dict[str, Callable]) -> Dict[str, Any]:
        """
        Выполнить несколько разных задач параллельно

        Args:
            tasks: Словарь {название: функция}

        Returns:
            Словарь {название: результат}
        """
        futures = {name: self.executor.submit(func) for name, func in tasks.items()}
        results = {}
        for name, future in futures.items():
            try:
                results[name] = future.result()
            except Exception as e:
                results[name] = None
        return results

    def shutdown(self):
        """Завершить executor"""
        self.executor.shutdown(wait=False)