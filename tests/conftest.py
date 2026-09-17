"""llm シェルのテスト用フィクスチャ。実 API は呼ばず、フェイクプロバイダを使う。"""
import io
import os
import hashlib
import pytest

from _kyodaishiki import __db__
from _kyodaishiki import __data__
from _kyodaishiki.shells import llm


class FakeLLMProvider(llm.LLMProvider):
	"""受け取った system / messages / tools を記録し、あらかじめ積んだ応答を返す。"""
	name = "fake"
	ENV_KEYS = ()
	instances = []

	def __init__(self, model, config):
		super().__init__(model, config)
		self.calls = []
		self.responses = []
		self.raise_exc = None
		FakeLLMProvider.instances.append(self)

	def queue(self, *responses):
		self.responses.extend(responses)

	def stream(self, system, messages, tools, output):
		self.calls.append({"system": system, "messages": [dict(m) for m in messages], "tools": tools})
		if self.raise_exc:
			exc, self.raise_exc = self.raise_exc, None
			raise exc
		resp = self.responses.pop(0) if self.responses else "OK"
		if isinstance(resp, str):
			resp = {"text": resp}
		text = resp.get("text", "")
		output.write(text)
		tool_uses = []
		content = [{"type": "text", "text": text}] if text else []
		for n, (name, input_) in enumerate(resp.get("tool_uses", [])):
			tid = "tu_{0}_{1}".format(len(self.calls), n)
			tool_uses.append(llm.ToolUse(tid, name, input_))
			content.append({"type": "tool_use", "id": tid, "name": name, "input": input_})
		return llm.Turn(text, tool_uses, content, llm.Usage(10, 5, 2), "tool_use" if tool_uses else resp.get("stop_reason", "end_turn"))


class FakeEmbeddingProvider(llm.EmbeddingProvider):
	"""文字の出現頻度から決定的なベクトルを作る。同じ文なら同じベクトル、似た文なら近い。"""
	name = "fake"
	ENV_KEYS = ()
	DIM = 64
	instances = []

	def __init__(self, model, config):
		super().__init__(model, config)
		self.query_calls = []
		self.document_calls = []
		FakeEmbeddingProvider.instances.append(self)

	@classmethod
	def vector(cls, text):
		v = [0.0] * cls.DIM
		for ch in text:
			v[ord(ch) % cls.DIM] += 1.0
		norm = sum(x * x for x in v) ** 0.5 or 1.0
		return [x / norm for x in v]

	def embed_documents(self, texts):
		self.document_calls.append(list(texts))
		return [self.vector(t) for t in texts]

	def embed_query(self, text):
		self.query_calls.append(text)
		return self.vector(text)

	def count_tokens(self, text):
		return max(1, len(text) // 2)


llm.LLM_PROVIDERS["fake"] = FakeLLMProvider
llm.EMBED_PROVIDERS["fake"] = FakeEmbeddingProvider

FAKE_OPTIONS = {"llm_provider": "fake", "llm_model": "fake-model", "embed_provider": "fake", "embed_model": "fake-embed"}

CARDS = {
	"NOTES": [
		("京大式カードは一枚一情報が原則である", "梅棹忠夫の知的生産の技術より", ["IDEA", "BOOK"], "2021-01-01 10:00:00"),
		("タグは大文字に正規化される", "実装メモ", ["IMPL"], "2021-02-01 10:00:00"),
		("ベクトル検索は意味の近さで探す", "RAG の話", ["RAG", "IDEA"], "2021-03-01 10:00:00"),
	],
	"BOOKS": [
		("知的生産の技術", "岩波新書", ["BOOK"], "2020-01-01 10:00:00"),
	],
}


def make_home(root, cards=CARDS):
	home_dir = os.path.join(str(root), "MAIN")
	home = __db__.HomeTagDB(home_dir)
	for dbid, items in cards.items():
		home.append(dbid, ["TEST"])
		db = home.select(dbid)
		for memo, comment, tags, date in items:
			db.appendCSM(__data__.CSM(memo, comment, tags, date))
		db.save()
	home.save()
	return home, home_dir


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
	for key in list(llm.ENV_KEYS.values()) + ["ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "VOYAGE_API_KEY", "KYODAISHIKI_LOADER_HOME"]:
		monkeypatch.delenv(key, raising=False)
	FakeLLMProvider.instances.clear()
	FakeEmbeddingProvider.instances.clear()
	yield


@pytest.fixture
def home(tmp_path):
	return make_home(tmp_path)


@pytest.fixture
def make_shell(home):
	"""LLMShell を生成するファクトリ。confirm の答えは confirm_answers で制御する。"""
	created = []

	def factory(options=None, confirm_answers=None, interactive=True, **kwargs):
		home_obj, home_dir = home
		opts = dict(FAKE_OPTIONS)
		opts.update(options or {})
		answers = list(confirm_answers or [])

		def confirm(message):
			return answers.pop(0) if answers else False
		shell = llm.LLMShell(home_obj, home_dir, opts, interactive=interactive, confirm_func=confirm if confirm_answers is not None else None, stdin=io.StringIO(), stdout=io.StringIO(), **kwargs)
		shell.confirm_answers = answers
		created.append(shell)
		return shell
	yield factory
	for s in created:
		try:
			s.close()
		except Exception:
			pass


def run(shell, line):
	"""1 行を実行し、出力文字列を返す。"""
	out = io.StringIO()
	shell.execLine(line, out)
	return out.getvalue()


@pytest.fixture
def chroma():
	return pytest.importorskip("chromadb")


def sha(text):
	return hashlib.sha1(text.encode()).hexdigest()[:16]
