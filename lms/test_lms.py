from lms import VideoItem, Quiz, ProgrammingAssigment, CompositeLearningItem

def test_composite_work():
	video_item_1 = VideoItem(name="Composite Design", length=20)
	video_item_2 = VideoItem(name="Composite Design v.2", length=10)
	lesson_composite = CompositeLearningItem(name="lesson on composite")
	lesson_composite.add(video_item_1)
	lesson_composite.add(video_item_2)
	exp_composite_time = 20 * 1.5 + 10 * 1.5
	assert exp_composite_time == lesson_composite.estimate_study_time()

	video_item_3 = VideoItem(name="Adapter Design", length=20)
	quiz = Quiz(name="Adapter Design", questions=20)
	lesson_adapter = CompositeLearningItem(name="lesson on adapter", learning_items=[video_item_3, quiz])
	exp_adapter_time = 20 * 1.5 + 20 * 5
	assert exp_adapter_time == lesson_adapter.estimate_study_time()

	module_design_pattern = CompositeLearningItem(name="Design Patterns", learning_items=[lesson_composite, lesson_adapter])
	module_design_pattern.add(ProgrammingAssigment(name="Factory method", language="python"))
	assert (exp_composite_time + exp_adapter_time + 120) == module_design_pattern.estimate_study_time()