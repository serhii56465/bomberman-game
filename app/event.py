import pygame
import abc

from mixins import EngineMixin


class Event(EngineMixin, abc.ABC):
    def __init__(self, ms_timeout):
        super().__init__()
        self.ms_timeout = ms_timeout

    @abc.abstractmethod
    def action(self):
        pass


class AddEnemy(Event):
    def __init__(self, ms_timeout, enemy_type):
        super().__init__(ms_timeout)

        self.event_no = pygame.USEREVENT + 1
        pygame.USEREVENT = self.event_no
        pygame.time.set_timer(self.event_no, self.ms_timeout)
        self.engine.add_event(self)
        self.enemy_type = enemy_type

    def action(self):
        self.enemy_type()
