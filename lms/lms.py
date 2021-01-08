from abc import ABC, abstractmethod


class LearningItem(ABC):
	def __init__(self, name):
		self.name = name

	@abstractmethod
	def estimate_study_time(self):
		raise NotImplementedError


class VideoItem(LearningItem):
	def __init__(self, name, length):
		super().__init__(name)
		self.length = length

	def estimate_study_time(self):
		return 1.5 * self.length


class Quiz(LearningItem):
	def __init__(self, name, questions):
		super().__init__(name)
		self.questions = questions

	def estimate_study_time(self):
		return 5 * self.questions


class ProgrammingAssigment(LearningItem):
	def __init__(self, name, language):
		super().__init__(name)
		self.language = language

	def estimate_study_time(self):
		return 120


class CompositeLearningItem(LearningItem):
	def __init__(self, name, learning_items=None):
		super().__init__(name)
		self.learning_items = []
		self.learning_items.extend(learning_items or [])

	def add(self, learning_item):
		self.learning_items.append(learning_item)

	def estimate_study_time(self):
		study_time = sum(
			learning_item.estimate_study_time()
			for learning_item in self.learning_items
		)
		return study_time
