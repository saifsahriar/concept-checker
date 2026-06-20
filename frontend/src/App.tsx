import { FormEvent, useEffect, useMemo, useState } from 'react';
import { Session } from '@supabase/supabase-js';
import { apiFetch } from './lib/api';
import { supabase } from './lib/supabase';

type SessionSummary = {
  id: string;
  concept: string;
  understanding_score: number | null;
  status: string;
  created_at: string;
};

type SessionDetail = {
  session: SessionSummary;
  responses: Array<{
    id: string;
    stage: string;
    question: string;
    answer: string | null;
    created_at: string;
  }>;
  analysis: null | {
    id: string;
    knowledge_gap: string;
    strengths: string;
    weaknesses: string;
    final_feedback: string;
    created_at: string;
  };
};

type InitialAnalysis = {
  knowledge_gap: string;
  strengths: string;
  weaknesses: string;
  followup_questions: string[];
};

type FollowupResult = {
  session_id: string;
  analysis: SessionDetail['analysis'];
  understanding_score: number;
  status: string;
};

function formatField(value: string | null | undefined) {
  if (!value) {
    return '';
  }
  const trimmed = value.trim();
  const listMatch = trimmed.match(/^\[(.*)\]$/s);
  if (listMatch) {
    const items = listMatch[1]
      .split(/',(?![^[]*\])/)
      .map((part) => part.replace(/^[\s'"]+|[\s'"]+$/g, '').trim())
      .filter(Boolean);
    if (items.length > 0) {
      return items.map((item) => `- ${item}`).join('\n');
    }
  }
  const dictMatch = trimmed.match(/^\{(.*)\}$/s);
  if (dictMatch) {
    return dictMatch[1]
      .split(/',(?![^{}]*\})/)
      .map((part) => part.replace(/^[\s'"]+|[\s'"]+$/g, '').trim())
      .filter(Boolean)
      .map((item) => item.replace(/:/, ': '))
      .join('\n');
  }
  return trimmed;
}

const emptyDetail: SessionDetail = {
  session: {
    id: '',
    concept: '',
    understanding_score: null,
    status: 'awaiting_initial_explanation',
    created_at: '',
  },
  responses: [],
  analysis: null,
};

function App() {
  const [authSession, setAuthSession] = useState<Session | null>(null);
  const [authMode, setAuthMode] = useState<'signin' | 'signup'>('signin');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [authError, setAuthError] = useState<string | null>(null);
  const [authBusy, setAuthBusy] = useState(false);
  const [history, setHistory] = useState<SessionSummary[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [activeDetail, setActiveDetail] = useState<SessionDetail>(emptyDetail);
  const [activeLoading, setActiveLoading] = useState(false);
  const [concept, setConcept] = useState('');
  const [explanation, setExplanation] = useState('');
  const [followupAnswers, setFollowupAnswers] = useState(['', '']);
  const [initialAnalysis, setInitialAnalysis] = useState<InitialAnalysis | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);

  useEffect(() => {
    if (!supabase) {
      return;
    }
    supabase.auth.getSession().then(({ data }) => setAuthSession(data.session ?? null));
    const { data } = supabase.auth.onAuthStateChange((_event, session) => setAuthSession(session));
    return () => data.subscription.unsubscribe();
  }, []);

  useEffect(() => {
    if (!authSession) {
      setHistory([]);
      setActiveSessionId(null);
      setActiveDetail(emptyDetail);
      setInitialAnalysis(null);
      setConcept('');
      setExplanation('');
      setFollowupAnswers(['', '']);
      setError(null);
      setInfo(null);
      return;
    }
    void loadHistory();
  }, [authSession]);

  const activeStage = useMemo(() => {
    if (!activeSessionId) {
      return 'start';
    }
    return activeDetail.session.status;
  }, [activeDetail.session.status, activeSessionId]);

  async function loadHistory() {
    setHistoryLoading(true);
    setError(null);
    try {
      const sessions = await apiFetch<SessionSummary[]>('/api/sessions');
      setHistory(sessions);
      if (sessions.length > 0 && !activeSessionId) {
        await openSession(sessions[0].id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load history');
    } finally {
      setHistoryLoading(false);
    }
  }

  async function openSession(sessionId: string) {
    setActiveLoading(true);
    setError(null);
    try {
      if (sessionId !== activeSessionId) {
        setInitialAnalysis(null);
      }
      const detail = await apiFetch<SessionDetail>(`/api/sessions/${sessionId}`);
      setActiveSessionId(sessionId);
      setActiveDetail(detail);
      const initialResponse = detail.responses.find((response) => response.stage === 'initial');
      const firstFollowup = detail.responses.find((response) => response.stage === 'followup_1');
      const secondFollowup = detail.responses.find((response) => response.stage === 'followup_2');
      setExplanation(initialResponse?.answer ?? '');
      setFollowupAnswers(['', '']);
      if (firstFollowup && secondFollowup) {
        setFollowupAnswers([firstFollowup.answer ?? '', secondFollowup.answer ?? '']);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load session');
    } finally {
      setActiveLoading(false);
    }
  }

  async function handleAuth(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!supabase) {
      setAuthError('Supabase is not configured. Add VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY.');
      return;
    }
    setAuthBusy(true);
    setAuthError(null);
    setInfo(null);
    try {
      if (authMode === 'signin') {
        const { error: signInError } = await supabase.auth.signInWithPassword({ email, password });
        if (signInError) {
          throw signInError;
        }
        setInfo('Signed in. Loading your sessions...');
      } else {
        const { data, error: signUpError } = await supabase.auth.signUp({ email, password });
        if (signUpError) {
          throw signUpError;
        }
        if (data.session) {
          setInfo('Account created and signed in.');
        } else {
          setInfo('Account created. Check your email to confirm the account, then sign in.');
        }
      }
    } catch (err) {
      setAuthError(err instanceof Error ? err.message : 'Authentication failed');
    } finally {
      setAuthBusy(false);
    }
  }

  async function handleCreateSession(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setInfo(null);
    try {
      const created = await apiFetch<{ session_id: string; concept: string; status: string; next_step: string }>('/api/sessions', {
        method: 'POST',
        body: JSON.stringify({ concept }),
      });
      setConcept('');
      setExplanation('');
      setInitialAnalysis(null);
      setFollowupAnswers(['', '']);
      await loadHistory();
      await openSession(created.session_id);
      setInfo('Session started. Add your explanation next.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to create session');
    }
  }

  async function handleInitialExplanation(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!activeSessionId) {
      return;
    }
    setError(null);
    setInfo(null);
    try {
      const analysis = await apiFetch<InitialAnalysis>(`/api/sessions/${activeSessionId}/initial-explanation`, {
        method: 'POST',
        body: JSON.stringify({ explanation }),
      });
      setInitialAnalysis(analysis);
      setFollowupAnswers(['', '']);
      setInfo('Follow-up questions are ready.');
      await openSession(activeSessionId);
      await loadHistory();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to save explanation');
    }
  }

  async function handleFollowups(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!activeSessionId) {
      return;
    }
    setError(null);
    setInfo(null);
    try {
      const result = await apiFetch<FollowupResult>(`/api/sessions/${activeSessionId}/followups`, {
        method: 'POST',
        body: JSON.stringify({ answers: followupAnswers }),
      });
      setInfo(`Final score: ${result.understanding_score}%`);
      await openSession(activeSessionId);
      await loadHistory();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to submit follow-up answers');
    }
  }

  async function signOut() {
    if (!supabase) {
      return;
    }
    await supabase.auth.signOut();
    setInitialAnalysis(null);
    setActiveSessionId(null);
    setActiveDetail(emptyDetail);
    setConcept('');
    setExplanation('');
    setFollowupAnswers(['', '']);
    setError(null);
    setInfo(null);
  }

  function startNewConversation() {
    setActiveSessionId(null);
    setActiveDetail(emptyDetail);
    setInitialAnalysis(null);
    setConcept('');
    setExplanation('');
    setFollowupAnswers(['', '']);
    setError(null);
    setInfo('Starting a new conversation.');
  }

  const currentQuestions = activeDetail.responses.filter((response) => response.stage.startsWith('followup_'));
  const initialResponse = activeDetail.responses.find((response) => response.stage === 'initial');
  const isComplete = activeDetail.session.status === 'complete';

  return (
    <div className="shell">
      <div className="backdrop" />
      <main className={`app ${!authSession ? 'auth-mode' : 'workspace-mode'}`}>
        <header className="hero">
          <div className="hero-content">
            <p className="eyebrow">Concept Checker</p>
            <h1>I help you understand any concept better</h1>
          </div>
          {authSession && (
            <div className="hero-actions">
              <button className="ghost-button" type="button" onClick={signOut}>
                Sign out
              </button>
            </div>
          )}
        </header>

        {!authSession ? (
          <section className="auth-panel">
            <div className="panel-header">
              <h2>{authMode === 'signin' ? 'Sign in' : 'Create account'}</h2>
              <button className="link-button" onClick={() => setAuthMode(authMode === 'signin' ? 'signup' : 'signin')}>
                {authMode === 'signin' ? 'Need an account?' : 'Already have an account?'}
              </button>
            </div>
            <form className="stack" onSubmit={handleAuth}>
              <label>
                Email
                <input value={email} onChange={(event) => setEmail(event.target.value)} type="email" required />
              </label>
              <label>
                Password
                <input value={password} onChange={(event) => setPassword(event.target.value)} type="password" required minLength={8} />
              </label>
              {authError ? <p className="error">{authError}</p> : null}
              <button className="primary-button" type="submit" disabled={authBusy}>
                {authBusy ? 'Working...' : authMode === 'signin' ? 'Sign in' : 'Create account'}
              </button>
            </form>
          </section>
        ) : (
          <section className="workspace">
            <aside className="sidebar">
              <div className="panel-header">
                <h2>Conversation history</h2>
              </div>
              {historyLoading ? <p className="muted">Loading history...</p> : null}
              <div className="history-list">
                {history.map((session) => (
                  <button
                    key={session.id}
                    type="button"
                    className={`history-card ${activeSessionId === session.id ? 'active' : ''}`}
                    onClick={() => void openSession(session.id)}
                  >
                    <strong>{session.concept}</strong>
                    <span>{session.status.replaceAll('_', ' ')}</span>
                    <span>{session.understanding_score == null ? 'Not scored yet' : `${session.understanding_score}%`}</span>
                  </button>
                ))}
                {history.length === 0 && !historyLoading ? <p className="muted">No sessions yet. Start with a concept on the right.</p> : null}
              </div>
            </aside>

            <section className="content">
              <div className="flow-panel">
                <div className="panel-header">
                  <div>
                    <p className="small-label">Active flow</p>
                    <h2>{activeSessionId ? activeDetail.session.concept : 'Start a new concept'}</h2>
                  </div>
                  <div className="header-actions">
                    {activeSessionId ? <span className="status-pill">{activeStage.replaceAll('_', ' ')}</span> : null}
                    {activeSessionId ? (
                      <button className="ghost-button" type="button" onClick={startNewConversation}>
                        New conversation
                      </button>
                    ) : null}
                  </div>
                </div>

                {error ? <p className="error">{error}</p> : null}
                {info ? <p className="success">{info}</p> : null}
                {activeLoading ? <p className="muted">Loading session...</p> : null}

                {!activeSessionId ? (
                  <form className="stack" onSubmit={handleCreateSession}>
                    <label>
                      Concept
                      <input
                        value={concept}
                        onChange={(event) => setConcept(event.target.value)}
                        placeholder="API, database, photosynthesis, Newton's laws..."
                        required
                      />
                    </label>
                    <button className="primary-button" type="submit">
                      Start session
                    </button>
                  </form>
                ) : (
                  <div className="flow">
                    <section className="step-card">
                      <div className="step-heading">
                        <span className="step-index">1</span>
                        <h3>Explain the concept</h3>
                      </div>
                      <form className="stack" onSubmit={handleInitialExplanation}>
                        <label>
                          Your explanation
                          <textarea
                            value={explanation || initialResponse?.answer || ''}
                            onChange={(event) => setExplanation(event.target.value)}
                            placeholder="Explain it like you're teaching a beginner."
                            rows={6}
                          />
                        </label>
                        <button className="primary-button" type="submit">
                          Save explanation
                        </button>
                      </form>
                    </section>

                    <section className="step-card">
                      <div className="step-heading">
                        <span className="step-index">2</span>
                        <h3>Answer the follow-ups</h3>
                      </div>
                      {initialAnalysis ? (
                        <div className="analysis-box">
                          <p>
                            <strong>Knowledge gap:</strong> {formatField(initialAnalysis.knowledge_gap)}
                          </p>
                          <p>
                            <strong>Strengths:</strong>
                            <span className="formatted-field">{formatField(initialAnalysis.strengths)}</span>
                          </p>
                          <p>
                            <strong>Weaknesses:</strong>
                            <span className="formatted-field">{formatField(initialAnalysis.weaknesses)}</span>
                          </p>
                        </div>
                      ) : null}
                      {isComplete ? (
                        <p className="success">This session is complete. The follow-up answers and report are locked in.</p>
                      ) : currentQuestions.length > 0 ? (
                        <form className="stack" onSubmit={handleFollowups}>
                          {currentQuestions.map((response, index) => (
                            <label key={response.id}>
                              {response.question}
                              <textarea
                                value={followupAnswers[index] ?? ''}
                                onChange={(event) => {
                                  const next = [...followupAnswers];
                                  next[index] = event.target.value;
                                  setFollowupAnswers(next);
                                }}
                                rows={4}
                              />
                            </label>
                          ))}
                          <button className="primary-button" type="submit">
                            Finish evaluation
                          </button>
                        </form>
                      ) : (
                        <p className="muted">Submit the explanation first to unlock the follow-up questions.</p>
                      )}
                    </section>

                    <section className="step-card">
                      <div className="step-heading">
                        <span className="step-index">3</span>
                        <h3>Final report</h3>
                      </div>
                      {activeDetail.analysis ? (
                        <div className="report">
                          <div className="score-chip">{activeDetail.session.understanding_score ?? 0}%</div>
                          <p>
                            <strong>Knowledge gap:</strong> {formatField(activeDetail.analysis.knowledge_gap)}
                          </p>
                          <p>
                            <strong>Strengths:</strong>
                            <span className="formatted-field">{formatField(activeDetail.analysis.strengths)}</span>
                          </p>
                          <p>
                            <strong>Weaknesses:</strong>
                            <span className="formatted-field">{formatField(activeDetail.analysis.weaknesses)}</span>
                          </p>
                          <p>
                            <strong>Feedback:</strong>
                            <span className="formatted-field">{formatField(activeDetail.analysis.final_feedback)}</span>
                          </p>
                        </div>
                      ) : (
                        <p className="muted">The final report appears after the follow-up answers are submitted.</p>
                      )}
                    </section>
                  </div>
                )}
              </div>
            </section>
          </section>
        )}
      </main>
    </div>
  );
}

export default App;
