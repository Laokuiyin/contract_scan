"""OCR Task Queue Manager"""

import threading
import time
from typing import Optional, Callable
from app.tasks.ocr_tasks import process_ocr


class OCRQueueManager:
    """单例模式的 OCR 任务队列管理器"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._queue = []
        self._current_task = None
        self._processing_lock = threading.Lock()
        self._worker_thread = None
        self._stop_event = threading.Event()

        # 启动工作线程
        self._start_worker()

    def _start_worker(self):
        """启动工作线程处理队列"""
        if self._worker_thread is None or not self._worker_thread.is_alive():
            self._stop_event.clear()
            self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self._worker_thread.start()
            print("OCR Queue Worker started")

    def _worker_loop(self):
        """工作线程主循环"""
        while not self._stop_event.is_set():
            try:
                # 获取下一个任务
                task = self._get_next_task()
                if task:
                    self._process_task(task)
                else:
                    # 没有任务时休眠
                    time.sleep(1)
            except Exception as e:
                print(f"Error in OCR queue worker: {e}")
                time.sleep(1)

    def _get_next_task(self) -> Optional[dict]:
        """从队列中获取下一个任务"""
        with self._processing_lock:
            if self._queue:
                return self._queue.pop(0)
            return None

    def _process_task(self, task: dict):
        """处理单个任务"""
        contract_id = task.get('contract_id')
        try:
            print(f"Processing OCR for contract: {contract_id}")
            self._current_task = task

            # 执行 OCR 任务
            result = process_ocr(contract_id)

            status = result.get('status', 'unknown')
            print(f"OCR completed for contract {contract_id}: {status}")

            # 可以在这里添加回调通知或其他逻辑

        except Exception as e:
            print(f"Error processing OCR for contract {contract_id}: {e}")
        finally:
            self._current_task = None

    def add_task(self, contract_id: str) -> dict:
        """
        添加任务到队列

        Args:
            contract_id: 合同 ID

        Returns:
            队列状态信息
        """
        with self._processing_lock:
            task = {
                'contract_id': contract_id,
                'added_time': time.time()
            }
            self._queue.append(task)

        return {
            'status': 'queued',
            'contract_id': contract_id,
            'queue_position': len(self._queue),
            'current_task': self._current_task.get('contract_id') if self._current_task else None
        }

    def get_queue_status(self) -> dict:
        """获取队列状态"""
        return {
            'queue_length': len(self._queue),
            'current_task': self._current_task.get('contract_id') if self._current_task else None,
            'queued_contracts': [task.get('contract_id') for task in self._queue]
        }

    def is_processing(self) -> bool:
        """检查是否有任务正在处理"""
        return self._current_task is not None

    def stop(self):
        """停止工作线程"""
        self._stop_event.set()
        if self._worker_thread:
            self._worker_thread.join(timeout=5)
            print("OCR Queue Worker stopped")


# 全局队列管理器实例
ocr_queue_manager = OCRQueueManager()
