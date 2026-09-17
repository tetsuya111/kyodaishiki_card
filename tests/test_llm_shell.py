import io
import os
import json
import pytest

from _kyodaishiki import __shell__
from _kyodaishiki.shells import llm
from conftest import FakeLLMProvider, run, sha


# ---------------------------------------------------------------------------
# Config / PromptTemplate（タスク2）
# ---------------------------------------------------------------------------

class TestConfig:
	def test_defaults_are_generated(self, tmp_path):
		cfg = llm.Config(str(tmp_path))
		assert cfg.llm_provider == "claude"
		assert cfg.embed_model == "voyage-4-large"
		data = json.load(open(tmp_path / "config.json", encoding="utf8"))
		assert data["top_k"] == 5

	def test_precedence_file_env_options(self, tmp_path, monkeypatch):
		(tmp_path / "config.json").write_text(json.dumps({"llm_model": "from-file", "top_k": 9}), encoding="utf8")
		monkeypatch.setenv("KYODAISHIKI_LLM_MODEL", "from-env")
		cfg = llm.Config(str(tmp_path))
		assert cfg.llm_model == "from-env"
		assert cfg.top_k == 9
		cfg2 = llm.Config(str(tmp_path), {"llm_model": "from-option", "embed_model": None})
		assert cfg2.llm_model == "from-option"
		assert cfg2.embed_model == "voyage-4-large"

	def test_existing_files_are_kept(self, tmp_path):
		(tmp_path / "config.json").write_text(json.dumps({"top_k": 3}), encoding="utf8")
		(tmp_path / "system_prompt.txt").write_text("custom prompt", encoding="utf8")
		llm.Config(str(tmp_path))
		assert json.load(open(tmp_path / "config.json", encoding="utf8"))["top_k"] == 3
		assert llm.PromptTemplate.load(str(tmp_path)) == "custom prompt"

	def test_prompt_template_default(self, tmp_path):
		text = llm.PromptTemplate.load(str(tmp_path))
		assert "京大式カード" in text
		assert (tmp_path / "system_prompt.txt").exists()

	def test_set_saves(self, tmp_path):
		cfg = llm.Config(str(tmp_path))
		cfg.set("tools_enabled", False)
		assert json.load(open(tmp_path / "config.json", encoding="utf8"))["tools_enabled"] is False


# ---------------------------------------------------------------------------
# プロバイダ（タスク3）
# ---------------------------------------------------------------------------

class TestProviders:
	def test_unknown_provider_lists_supported(self, tmp_path):
		cfg = llm.Config(str(tmp_path))
		with pytest.raises(llm.ProviderError) as e:
			llm.make_provider(llm.LLM_PROVIDERS, "gpt", "x", cfg, "LLM ")
		assert "claude" in str(e.value) and "fake" in str(e.value)

	def test_claude_credentials(self, tmp_path, monkeypatch):
		cfg = llm.Config(str(tmp_path))
		p = llm.ClaudeProvider("claude-opus-5", cfg)
		with pytest.raises(llm.CredentialError) as e:
			p.check_credentials()
		assert "ANTHROPIC_API_KEY" in str(e.value)
		monkeypatch.setenv("ANTHROPIC_AUTH_TOKEN", "x")
		p.check_credentials()

	def test_voyage_credentials(self, tmp_path, monkeypatch):
		cfg = llm.Config(str(tmp_path))
		p = llm.VoyageProvider("voyage-4-large", cfg)
		with pytest.raises(llm.CredentialError) as e:
			p.check_credentials()
		assert "VOYAGE_API_KEY" in str(e.value)
		monkeypatch.setenv("VOYAGE_API_KEY", "x")
		p.check_credentials()

	def test_shell_rejects_unknown_provider(self, home):
		home_obj, home_dir = home
		with pytest.raises(llm.ProviderError):
			llm.LLMShell(home_obj, home_dir, {"llm_provider": "nope", "embed_provider": "fake"}, stdout=io.StringIO())

	def test_shell_without_credentials_disables_chat(self, home):
		home_obj, home_dir = home
		shell = llm.LLMShell(home_obj, home_dir, {"llm_provider": "claude", "embed_provider": "fake"}, stdout=io.StringIO())
		assert "ANTHROPIC_API_KEY" in shell.llm_error
		out = run(shell, "こんにちは")
		assert "ANTHROPIC_API_KEY" in out


# ---------------------------------------------------------------------------
# Chunker（タスク4）
# ---------------------------------------------------------------------------

class TestChunker:
	@staticmethod
	def count(text):
		return len(text)

	def test_empty(self):
		assert llm.Chunker(self.count, 10).split("") == []

	def test_single_chunk(self):
		assert llm.Chunker(self.count, 100).split("short text") == ["short text"]

	def test_paragraph_split_and_join(self):
		text = "aaaa\n\nbbbb\n\ncccc\n\ndddd"
		chunks = llm.Chunker(self.count, 12).split(text)
		assert chunks == ["aaaa\n\nbbbb\n\n", "cccc\n\ndddd"]
		assert "".join(chunks) == text

	def test_line_split_when_paragraph_too_long(self):
		text = "l1\nl2\nl3\nl4\n\nend"
		chunks = llm.Chunker(self.count, 6).split(text)
		assert all(self.count(c) <= 6 for c in chunks)
		assert "".join(chunks) == text
		assert len(chunks) > 2

	def test_sentence_and_char_split(self):
		text = "あいう。えおか。きくけこさしすせそたちつてと"
		chunks = llm.Chunker(self.count, 5).split(text)
		assert all(self.count(c) <= 5 for c in chunks)
		assert "".join(chunks) == text


# ---------------------------------------------------------------------------
# ContextBuilder
# ---------------------------------------------------------------------------

def hit(dbid, text, score=0.9):
	return llm.CardHit(dbid, sha(text), score, text, {"date": "2021", "tags": "T"}, [(0, score, text)])


class TestContextBuilder:
	def test_empty(self):
		text, used = llm.ContextBuilder.build([], 5, 1000)
		assert text == llm.ContextBuilder.EMPTY and used == []

	def test_max_cards(self):
		hits = [hit("A", "x" * 10), hit("B", "y" * 10), hit("C", "z" * 10)]
		text, used = llm.ContextBuilder.build(hits, 2, 10000)
		assert len(used) == 2 and "[2] DB: B" in text and "DB: C" not in text

	def test_max_chars_reduces_count(self):
		hits = [hit("A", "x" * 100), hit("B", "y" * 100), hit("C", "z" * 100)]
		text, used = llm.ContextBuilder.build(hits, 5, 260)
		assert len(used) == 1
		text2, used2 = llm.ContextBuilder.build(hits, 5, 30)
		assert len(used2) == 1 and len(text2) <= 30 + len(llm.ContextBuilder.TAIL)


# ---------------------------------------------------------------------------
# コマンド体系（タスク7）
# ---------------------------------------------------------------------------

class TestDispatch:
	def test_help(self, make_shell):
		shell = make_shell()
		out = run(shell, "/help")
		assert "/rag add" in out and "/quit" in out

	def test_unknown_command_not_sent_to_llm(self, make_shell):
		shell = make_shell()
		out = run(shell, "/nope arg")
		assert "unknown command: /nope" in out
		assert run(shell, "/").startswith("unknown command")
		assert shell.llm.calls == []

	def test_plain_line_is_chat_verbatim(self, make_shell):
		shell = make_shell()
		shell.llm.queue("answer")
		out = run(shell, "Hello  World  こんにちは")
		assert "answer" in out
		sent = shell.llm.calls[0]["messages"][-1]["content"]
		assert sent.endswith("Hello  World  こんにちは")
		assert shell.history[0]["content"] == "Hello  World  こんにちは"

	def test_double_slash_escapes(self, make_shell):
		shell = make_shell()
		shell.llm.queue("ok")
		run(shell, "//usr/bin について")
		assert shell.history[0]["content"] == "/usr/bin について"

	def test_quit_raises_exit(self, make_shell):
		shell = make_shell()
		with pytest.raises(__shell__.ExitShell):
			run(shell, "/quit")
		with pytest.raises(__shell__.ExitShell):
			run(shell, "/q")

	def test_base_commands_with_slash(self, make_shell):
		shell = make_shell()
		run(shell, "/alias hi /rag ls")
		assert "HI" in shell.aliasCommands

	def test_model_and_usage(self, make_shell):
		shell = make_shell()
		out = run(shell, "/model")
		assert "fake / fake-model" in out and "fake/fake-embed" in out
		assert "last  : -" in run(shell, "/usage")
		shell.llm.queue("a")
		run(shell, "q1")
		out = run(shell, "/usage")
		assert "input=10 output=5" in out

	def test_pipe_redirect(self, make_shell, tmp_path):
		shell = make_shell()
		target = tmp_path / "out.txt"
		run(shell, "/model > " + str(target))
		assert "fake-model" in target.read_text(encoding="utf8")

	def test_error_in_provider_keeps_shell(self, make_shell):
		shell = make_shell()
		shell.llm.raise_exc = RuntimeError("boom")
		out = run(shell, "hello")
		assert "[error]" in out and "boom" in out
		shell.llm.queue("fine")
		assert "fine" in run(shell, "again")


# ---------------------------------------------------------------------------
# RAG 登録・検索（タスク5・6）
# ---------------------------------------------------------------------------

class TestRag:
	def test_add_list_remove(self, make_shell, chroma):
		shell = make_shell()
		out = run(shell, "/rag add notes")
		assert "registered NOTES: 3 cards / 3 chunks (3 cards re-indexed)" in out
		assert "3/3 cards" in out
		out = run(shell, "/rag ls")
		assert "NOTES" in out and "cards=3" in out and "fake/fake-embed" in out
		out = run(shell, "/rag add notes")
		assert "(0 cards re-indexed)" in out
		out = run(shell, "/rag rm notes")
		assert "removed NOTES" in out
		assert "(no DB registered)" in run(shell, "/rag ls")
		assert shell.store.count() == 0

	def test_add_unknown_db(self, make_shell, chroma):
		shell = make_shell()
		assert "DB not found: NOPE" in run(shell, "/rag add nope")

	def test_wildcard(self, make_shell, chroma):
		shell = make_shell()
		out = run(shell, "/rag add *")
		assert "registered NOTES" in out and "registered BOOKS" in out
		assert shell.store.count() == 4

	def test_incremental_update_and_delete(self, make_shell, home, chroma):
		shell = make_shell()
		run(shell, "/rag add notes")
		home_obj, _ = home
		db = home_obj.select("NOTES")
		cards = list(db.search())
		target = [c for c in cards if "タグは大文字" in c.memo(db.text)][0]
		db.remove(target.id)
		from _kyodaishiki import __data__
		db.appendCSM(__data__.CSM("新しいカード", "追加", ["NEW"], "2022-01-01 00:00:00"))
		db.save()
		out = run(shell, "/rag add notes")
		assert "(1 cards re-indexed)" in out
		ids = [c["metadata"]["card_id"] for c in shell.store.get_chunks("NOTES")]
		assert sha("新しいカード") in ids and sha("タグは大文字に正規化される") not in ids
		assert shell.store.count("NOTES") == 3

	def test_model_mismatch_warns_and_reindexes(self, make_shell, chroma):
		shell = make_shell()
		run(shell, "/rag add notes")
		shell.registry.set("NOTES", dict(shell.registry.get("NOTES"), embed_model="old-model"))
		shell2 = make_shell()
		assert "!" in run(shell2, "/rag ls").splitlines()[0]
		out = run(shell2, "/rag search カード")
		assert "[warn] 埋め込みモデル" in out
		out = run(shell2, "/rag add notes")
		assert "(3 cards re-indexed)" in out

	def test_search_ranks_exact_memo_first(self, make_shell, chroma):
		shell = make_shell()
		run(shell, "/rag add *")
		out = run(shell, "/rag search ベクトル検索は意味の近さで探す")
		first = out.splitlines()[0]
		assert first.startswith("[1]") and "DB:notes" in first
		assert "ベクトル検索は意味の近さで探す" in out.splitlines()[1]

	def test_search_filters_and_limits(self, make_shell, chroma):
		shell = make_shell()
		run(shell, "/rag add *")
		out = run(shell, "/rag search -D books -n 1 知的生産の技術")
		assert out.count("score=") == 1 and "DB:books" in out
		out = run(shell, "/rag search -n 2 カード")
		assert out.count("score=") == 2

	def test_search_empty_store(self, make_shell, chroma):
		shell = make_shell()
		assert "/rag add" in run(shell, "/rag search x")

	def test_multichunk_card_grouped(self, make_shell, home, chroma):
		home_obj, _ = home
		db = home_obj.select("NOTES")
		from _kyodaishiki import __data__
		long_memo = "長いカード"
		db.appendCSM(__data__.CSM(long_memo, "\n\n".join("段落{0} ".format(i) * 5 for i in range(6)), ["LONG"], "2023-01-01 00:00:00"))
		db.save()
		shell = make_shell()
		shell.config.set("chunk_tokens", 20)
		run(shell, "/rag add notes")
		cid = sha(long_memo)
		chunks = shell.store.get_chunks("NOTES", cid)
		assert len(chunks) > 1
		out = run(shell, "/rag search -n 10 長いカード 段落3 段落4")
		assert out.count("id=" + cid) == 1
		full = "".join(c["document"] for c in sorted(chunks, key=lambda c: c["metadata"]["chunk"]))
		assert full.startswith(long_memo) and "hit chunk" in out

	def test_embedding_unavailable(self, home):
		home_obj, home_dir = home
		shell = llm.LLMShell(home_obj, home_dir, {"llm_provider": "fake", "embed_provider": "voyage"}, stdout=io.StringIO())
		assert "VOYAGE_API_KEY" in run(shell, "/rag add notes")
		assert "VOYAGE_API_KEY" in run(shell, "/rag search x")
		shell.llm.queue("ok")
		out = run(shell, "hello")
		assert "ok" in out and shell.embedder.__class__.__name__ == "VoyageProvider"


# ---------------------------------------------------------------------------
# RAG を用いた対話（タスク8）
# ---------------------------------------------------------------------------

class TestChatRag:
	def test_search_each_turn_and_context(self, make_shell, chroma):
		shell = make_shell()
		run(shell, "/rag add notes")
		shell.llm.queue("a1", "a2")
		out = run(shell, "京大式カードについて")
		assert "(参照カード:" in out
		run(shell, "もう一度")
		assert shell.embedder.query_calls == ["京大式カードについて", "もう一度"]
		sent = shell.llm.calls[0]["messages"][-1]["content"]
		assert sent.startswith("<cards>") and "京大式カード" in sent and sent.endswith("京大式カードについて")
		assert shell.llm.calls[1]["messages"][0]["content"] == "京大式カードについて"
		assert "last" in run(shell, "/usage")
		assert "DB:notes" in run(shell, "/rag last")

	def test_rag_off(self, make_shell, chroma):
		shell = make_shell()
		run(shell, "/rag add notes")
		run(shell, "/rag off")
		shell.llm.queue("a")
		run(shell, "hello")
		assert shell.embedder.query_calls == []
		assert shell.llm.calls[0]["messages"][-1]["content"] == "hello"
		assert "rag: off" in run(shell, "/model").lower() or "RAG       : off" in run(shell, "/model")

	def test_rag_use_limits_db(self, make_shell, chroma):
		shell = make_shell()
		run(shell, "/rag add *")
		assert "rag use: BOOKS" in run(shell, "/rag use books")
		shell.llm.queue("a")
		run(shell, "知的生産の技術")
		assert all(h.dbid == "BOOKS" for h in shell.last_hits) and shell.last_hits
		assert "rag use: (all)" in run(shell, "/rag use")
		assert "DB not found" in run(shell, "/rag use zzz")

	def test_no_registered_cards_still_chats(self, make_shell, chroma):
		shell = make_shell()
		shell.llm.queue("a")
		out = run(shell, "hello")
		assert "RAG に登録されたカードがありません" in out and "a" in out
		assert llm.ContextBuilder.EMPTY in shell.llm.calls[0]["messages"][-1]["content"]

	def test_system_prompt_is_sent(self, make_shell):
		shell = make_shell()
		shell.llm.queue("a")
		run(shell, "x")
		assert "京大式カード" in shell.llm.calls[0]["system"]

	def test_history_and_clear(self, make_shell):
		shell = make_shell()
		shell.llm.queue("a1", "a2")
		run(shell, "q1")
		run(shell, "q2")
		assert len(shell.history) == 4
		assert len(shell.llm.calls[1]["messages"]) == 3
		out = run(shell, "/clear")
		assert "new session" in out and shell.history == []


# ---------------------------------------------------------------------------
# 自然言語からのコマンド実行（タスク8b）
# ---------------------------------------------------------------------------

class TestTools:
	def test_definitions_exclude_control_commands(self, make_shell):
		shell = make_shell()
		names = shell.tool_registry.names()
		assert "rag_add" in names and "rag_search" in names
		for forbidden in ("sh", "exec", "clear", "quit", "tools", "map", "xargs", "alias"):
			assert forbidden not in names
		for d in shell.tool_registry.definitions():
			assert d["input_schema"]["additionalProperties"] is False
			cmd = shell.tool_registry.to_command(d["name"], {"dbids": ["X"], "query": "q", "id": "i", "enabled": True})
			assert cmd.split()[0] in ("/rag", "/model", "/usage", "/history")

	def test_to_command(self, make_shell):
		reg = llm.ToolRegistry()
		assert reg.to_command("rag_add", {"dbids": ["NOTES", "my db"]}) == '/rag add NOTES "my db"'
		assert reg.to_command("rag_search", {"query": "京大式 カード", "dbid": "NOTES", "n": 3}) == '/rag search -D NOTES -n 3 "京大式 カード"'
		assert reg.to_command("rag_toggle", {"enabled": False}) == "/rag off"
		assert reg.to_command("rag_use", {}) == "/rag use"
		assert reg.to_command("nope", {}) is None

	def test_approved_tool_runs_and_result_returned(self, make_shell, chroma):
		shell = make_shell(confirm_answers=[True])
		shell.llm.queue({"text": "登録します。", "tool_uses": [("rag_add", {"dbids": ["notes"]})]}, "登録しました。")
		out = run(shell, "notes を RAG に登録して")
		assert "/rag add notes" in out and "registered NOTES" in out and "登録しました。" in out
		assert len(shell.llm.calls) == 2
		results = shell.llm.calls[1]["messages"][-1]["content"]
		assert results[0]["type"] == "tool_result" and "registered NOTES" in results[0]["content"]
		assert shell.llm.calls[1]["messages"][-2]["content"][-1]["type"] == "tool_use"
		assert shell.store.count("NOTES") == 3
		recs = shell.history_store.read(shell.history_store.session_id)
		tool_recs = [r for r in recs if r["role"] == "tool"]
		assert tool_recs and tool_recs[0]["approved"] is True and tool_recs[0]["command"] == "/rag add notes"

	def test_denied_tool_not_run(self, make_shell, chroma):
		shell = make_shell(confirm_answers=[False])
		shell.llm.queue({"tool_uses": [("rag_add", {"dbids": ["notes"]})]}, "わかりました。")
		out = run(shell, "登録して")
		assert "拒否しました" in out
		results = shell.llm.calls[1]["messages"][-1]["content"]
		assert "拒否" in results[0]["content"] and "is_error" not in results[0]
		assert shell.registry.get("NOTES") is None
		recs = [r for r in shell.history_store.read(shell.history_store.session_id) if r["role"] == "tool"]
		assert recs[0]["approved"] is False

	@pytest.mark.parametrize("answer,expected", [("y\n", True), ("YES\n", True), ("Yes\n", True), ("n\n", False), ("\n", False), ("", False), ("ok\n", False)])
	def test_confirm_only_accepts_yes(self, make_shell, answer, expected):
		shell = make_shell()
		shell.stdin = io.StringIO(answer)
		assert shell.confirm("実行しますか? (y/n): ") is expected

	def test_confirm_non_interactive_denies(self, make_shell):
		shell = make_shell(interactive=False)
		shell.stdin = io.StringIO("y\n")
		assert shell.confirm("?") is False

	def test_multiple_tool_uses_confirmed_in_order(self, make_shell, chroma):
		shell = make_shell(confirm_answers=[True, False])
		shell.llm.queue({"tool_uses": [("rag_list", {}), ("rag_remove", {"dbids": ["notes"]})]}, "done")
		out = run(shell, "一覧を見せてから notes を消して")
		assert out.index("/rag ls") < out.index("/rag rm notes")
		results = shell.llm.calls[1]["messages"][-1]["content"]
		assert len(results) == 2 and "拒否" in results[1]["content"] and "拒否" not in results[0]["content"]

	def test_max_rounds(self, make_shell):
		shell = make_shell(confirm_answers=[True] * 10)
		shell.config.set("tool_max_rounds", 2)
		shell.llm.queue(*[{"tool_uses": [("rag_last", {})]}] * 3, "end")
		run(shell, "loop")
		assert len(shell.llm.calls) == 4
		last_results = shell.llm.calls[3]["messages"][-1]["content"]
		assert "上限" in last_results[0]["content"]
		assert shell.llm.calls[3]["tools"] is None

	def test_tools_off_sends_no_tools(self, make_shell):
		shell = make_shell()
		shell.llm.queue("a")
		run(shell, "x")
		assert shell.llm.calls[0]["tools"]
		assert "tools: off" in run(shell, "/tools off")
		shell.llm.queue("b")
		run(shell, "y")
		assert shell.llm.calls[1]["tools"] is None
		assert json.load(open(os.path.join(shell.llm_dname, "config.json"), encoding="utf8"))["tools_enabled"] is False

	def test_tool_error_is_reported(self, make_shell):
		shell = make_shell(confirm_answers=[True])
		shell.llm.queue({"tool_uses": [("history_show", {"id": "nope"})]}, "sorry")
		run(shell, "show history nope")
		results = shell.llm.calls[1]["messages"][-1]["content"]
		assert "not found" in results[0]["content"]


# ---------------------------------------------------------------------------
# 履歴（タスク9）
# ---------------------------------------------------------------------------

class TestHistory:
	def test_history_store_roundtrip(self, tmp_path):
		store = llm.HistoryStore(str(tmp_path))
		sid = store.new_session()
		store.append({"role": "user", "content": "first\nsecond", "cards": []})
		store.append({"role": "assistant", "content": "answer", "usage": {"input_tokens": 1}})
		assert store.list() == [(sid, "first")]
		recs = store.read(sid)
		assert [r["role"] for r in recs] == ["user", "assistant"] and "ts" in recs[0]
		assert store.remove(sid) and store.list() == [] and not store.remove(sid)

	def test_history_commands(self, make_shell):
		shell = make_shell()
		shell.llm.queue("a1")
		run(shell, "q1")
		sid = shell.history_store.session_id
		assert sid in run(shell, "/history ls")
		out = run(shell, "/history show " + sid)
		assert "q1" in out and "a1" in out
		run(shell, "/clear")
		assert shell.history_store.session_id != sid
		assert "removed" in run(shell, "/history rm " + sid)
		assert "not found" in run(shell, "/history show " + sid)

	def test_clear_keeps_file(self, make_shell):
		shell = make_shell()
		shell.llm.queue("a")
		run(shell, "q")
		sid = shell.history_store.session_id
		run(shell, "/clear")
		assert shell.history_store.exists(sid)


# ---------------------------------------------------------------------------
# 子シェル統合・非対話（タスク10・11）
# ---------------------------------------------------------------------------

class FakeHomeShell:
	def __init__(self, home, dname):
		self.home = home
		self.dname = dname
		self.stdin = io.StringIO()
		self.stdout = io.StringIO()


class TestAuHSShell:
	def test_options_and_command(self, home, monkeypatch):
		home_obj, home_dir = home
		monkeypatch.setenv("KYODAISHIKI_EMBED_PROVIDER", "fake")
		au = llm.AuHSShell(FakeHomeShell(home_obj, home_dir))
		out = io.StringIO()
		au.execQuery(llm.Query(["--llm", "fake", "--model", "m1", "/model"]), out)
		assert "fake / m1" in out.getvalue()
		assert au.shell_.config.llm_model == "m1"

	def test_chat_via_args(self, home, monkeypatch):
		home_obj, home_dir = home
		monkeypatch.setenv("KYODAISHIKI_LLM_PROVIDER", "fake")
		monkeypatch.setenv("KYODAISHIKI_EMBED_PROVIDER", "fake")
		au = llm.AuHSShell(FakeHomeShell(home_obj, home_dir))
		out = io.StringIO()
		au.execQuery(llm.Query(["hello", "there"]), out)
		assert au.shell_.llm.calls[0]["messages"][-1]["content"].endswith("hello there")

	def test_unknown_provider_reported(self, home):
		home_obj, home_dir = home
		au = llm.AuHSShell(FakeHomeShell(home_obj, home_dir))
		out = io.StringIO()
		au.execQuery(llm.Query(["--llm", "nope", "/model"]), out)
		assert "未対応" in out.getvalue()

	def test_start_interactive_session(self, home):
		home_obj, home_dir = home
		hs = FakeHomeShell(home_obj, home_dir)
		hs.stdin = io.StringIO("/model\n/quit\n")
		au = llm.AuHSShell(hs)
		au.execQuery(llm.Query(["--llm", "fake", "--embed", "fake"]), hs.stdout)
		out = hs.stdout.getvalue()
		assert "*** llm" in out and "fake / claude-opus-5" in out and "fake/voyage-4-large" in out


class TestMain:
	def test_main_command(self, home, monkeypatch):
		home_obj, home_dir = home
		home_obj.close()
		monkeypatch.setenv("KYODAISHIKI_LLM_PROVIDER", "fake")
		monkeypatch.setenv("KYODAISHIKI_EMBED_PROVIDER", "fake")
		out = io.StringIO()
		assert llm.main(["--home-dir", home_dir, "/rag", "ls"], out) == 0
		assert "no DB registered" in out.getvalue()

	def test_main_chat_denies_tools(self, home, monkeypatch, chroma):
		home_obj, home_dir = home
		home_obj.close()
		monkeypatch.setenv("KYODAISHIKI_LLM_PROVIDER", "fake")
		monkeypatch.setenv("KYODAISHIKI_EMBED_PROVIDER", "fake")
		out = io.StringIO()
		FakeLLMProvider.instances.clear()
		import conftest
		orig_init = FakeLLMProvider.__init__

		def init(self, model, config):
			orig_init(self, model, config)
			self.queue({"tool_uses": [("rag_add", {"dbids": ["notes"]})]}, "done")
		monkeypatch.setattr(FakeLLMProvider, "__init__", init)
		assert llm.main(["--home-dir", home_dir, "notes", "を登録して"], out) == 0
		text = out.getvalue()
		assert "拒否しました" in text and "done" in text
		assert conftest.FakeEmbeddingProvider.instances[0].document_calls == []

	def test_main_usage(self):
		out = io.StringIO()
		assert llm.main([], out) == 2 and "Usage" in out.getvalue()
		assert llm.main(["--home-dir"], out) == 2

	def test_default_home_dir(self, monkeypatch, tmp_path):
		monkeypatch.setenv("KYODAISHIKI_LOADER_HOME", str(tmp_path))
		assert llm.default_home_dir() == os.path.join(str(tmp_path), "MAIN")
