try:
	from app.guardrails.rails import initialize_rails, guard
except ModuleNotFoundError:
	def initialize_rails() -> None:
		return

	def guard(message: str) -> tuple[bool, str | None]:
		return False, None