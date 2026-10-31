from pydantic import BaseModel, model_validator


class TestCase(BaseModel):
    id: str
    prompt: str
    expected_behaviour: str
    tags: list[str] = []
    model: str | None = None


class EvalSuite(BaseModel):
    name: str
    description: str = ""
    default_model: str | None = None
    cases: list[TestCase]

    @model_validator(mode="after")
    def _unique_ids(self) -> "EvalSuite":
        ids = [c.id for c in self.cases]
        dupes = {i for i in ids if ids.count(i) > 1}
        if dupes:
            raise ValueError(f"Duplicate test case ids: {dupes}")
        return self
