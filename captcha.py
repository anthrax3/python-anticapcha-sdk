import base64
from enum import Enum

import requests

HOST_ADDRESS = 'https://api.anti-captcha.com/{}'


class CaptchaException(Exception):
    """
    If any error occurs during solving captcha
    """
    pass


class Queue(Enum):
    STANDARD_ENG = 1
    STANDARD_RUS = 1
    RECAPTCHA = 5
    RECAPTCHA_PROXYLESS = 6
    FUNCAPTCHA = 7
    FUNCAPTCHA_PROXYLESS = 8


class Numeric(Enum):
    NO_REQUIREMENTS = 0
    ONLY_NUMBERS = 1
    ONLY_LETTERS = 2


class LanguagePool(Enum):
    """
    Sets workers pool language
    """
    ENGLISH = 'en'
    RUSSIAN = 'rn'


class Task:
    def __init__(self, task_type: str):
        self.data = {'type': task_type}

    @staticmethod
    def base64_encode(url: str) -> str:
        return base64.b64encode(requests.get(url).content).decode()

    def build(self) -> dict:
        data = {}
        for k, v in self.data.items():
            if v is not None:
                data[k] = v
        return data


class ImageToTextTask(Task):
    """
    Usual image captcha.

    Parameters
    ----------
    phrase : bool : False
        If true, worker must enter an answer with at least one "space"
    case : bool : False
        If true, worker will see a special mark telling that answer must be entered with case sensitivity
    numeric : :class:`Numeric` : :class:`Numeric.NO_REQUIREMENTS`
        Answers must be entered with only letters, numbers or none
    math : bool : False
        If true, worker will see a special mark telling that answer must be calculated
    min_length : int : 0
        Defines minimum length of the answer
    min_length : int : 0
        Defines maximum length of the answer
    """

    def __init__(self, image_url: str, phrase: bool = None, case: bool = None, numeric: Numeric = None,
                 math: bool = None, min_length: int = None, max_length: int = None):
        super().__init__('ImageToTextTask')
        self.data.update({
            'body': self.base64_encode(image_url),
            'phrase': phrase,
            'case': case,
            'numeric': numeric.value if numeric else None,
            'math': math,
            'minLength': min_length,
            'maxLength': max_length
        })


class AntiCaptchaService:
    """
    Class for solving captcha's using anti-captcha service https://anti-captcha.com.

    Parameters
    ----------
    client_key : str
        The client's API key, can be obtained in profile on site
    soft_id : int
        ID of your application from out AppCenter,
        this is required to earn 10% from clients spending's which use your application
    """

    def __init__(self, client_key: str, soft_id: int = None):
        self.client_key = client_key
        self.soft_id = soft_id

    @staticmethod
    def __request(method, data):
        response = requests.post(HOST_ADDRESS.format(method), json=data).json()
        if 'errorId' in response:
            if response['errorId'] > 0:
                raise CaptchaException('{} ({}): {}'.format(
                    response['errorId'], response['errorCode'], response['errorDescription']))
            del response['errorId']
        return response

    def get_balance(self) -> float:
        """
        Retrieve account balance.

        Returns
        -------
        float
            Account balance in USD
        """
        data = {'clientKey': self.client_key}
        return self.__request('getBalance', data)['balance']

    def get_queue_stats(self, queue_id: Queue) -> dict:
        """
        Retrieve account balance.

        Parameters
        ----------
        queue_id : :class:`Queue`
            Identifier of required queue

        Returns
        -------
        dict
            waiting : int
                Amount of idle workers online, waiting for a task
            load : float
                Queue load in percents
            bid : float
                Average task solution cost in USD
            speed : float
                Average task solution speed in seconds
            total : int
                Total number of workers
        """
        data = {'clientKey': self.client_key, 'queueId': queue_id.value}
        return self.__request('getQueueStats', data)

    def create_task(self, task: Task, lang_pool: LanguagePool = LanguagePool.ENGLISH, callback_url: str = None) -> int:
        """
        Creates a task for solving selected captcha type.

        Parameters
        ----------
        task : :class:`Task`
            Task data object
        lang_pool : :class:`LanguagePool` : class:`LanguagePool.ENGLISH`
            Sets workers pool language
        callback_url : str : None
            Optional web address were will send result of captcha/factory task processing.
            Contents are sent by AJAX POST request and are similar
            to the contents of :func:`::get_task_result(task_id)` method

        Returns
        -------
        int
            Task ID for future use in :func:`::get_task_result(task_id)` method
        """
        data = {'clientKey': self.client_key, 'languagePool': lang_pool.value, 'task': task.build()}
        if callback_url is not None:
            data['callbackUrl'] = callback_url
        if self.soft_id is not None:
            data['softId'] = self.soft_id
        return self.__request('createTask', data)['taskId']

    def get_task_result(self, task_id: int) -> dict:
        """
        Returns the result of required task.

        Parameters
        ----------
        task_id : :class:`Task`
            ID which was obtained in :func:`::create_task(task, lang_pool, callback_url)` method

        Returns
        -------
        dict
            status : bool
                Task is ready or not
            solution : dict
                Task result data. Different for each type of task
            cost : float
                Task cost in USD
            ip : str
                IP from which the task was created
            createTime : int
                UNIX Timestamp of task creation
            endTime : int
                UNIX Timestamp of task completion
            solveCount : int
                Number of workers who tried to complete your task
        """
        data = {'clientKey': self.client_key, 'taskId': task_id}
        response = self.__request('getTaskResult', data)
        response['status'] = response['status'] == 'ready'
        return response

    def report(self, task_id: int) -> bool:
        """
        Complaints are accepted only for image captcha's.
        Your complaint will be checked by 5 workers, 3 of them must confirm it.
        Only then you get full refund. If you have less than 20% confirmation ratio,
        your reports will be ignored.

        Parameters
        ----------
        task_id : :class:`Task`
            ID which was obtained in :func:`::create_task(task, lang_pool, callback_url)` method

        Returns
        -------
        bool
            True if complaint accepted, otherwise False
        """
        data = {'clientKey': self.client_key, 'taskId': task_id}
        return self.__request('reportIncorrectImageCaptcha', data)['status'] == 'success'
