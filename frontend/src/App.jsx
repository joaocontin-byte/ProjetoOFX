import { useRef, useState } from "react";
import { ArrowDownLeft, ArrowUpRight, Check, ChevronDown, CircleHelp, FileUp, Download, Landmark, LoaderCircle, Plus, Search, ShieldCheck, Sparkles, Upload, Wallet, X } from "lucide-react";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";
const CATEGORY_STORAGE_KEY = "projeto-ofx-categorias";
const brl = (value) => new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value || 0);
const datePt = (value) => new Date(`${value}T12:00:00`).toLocaleDateString("pt-BR");
const colors = {};

export default function App() {
  const inputRef = useRef(null);
  const [report, setReport] = useState(null);
  const [busy, setBusy] = useState(false);
  const [saving, setSaving] = useState(false);
  const [exporting, setExporting] = useState(null);
  const [notice, setNotice] = useState(null);
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("Todas as categorias");
  const [bank, setBank] = useState("idle");
  const [helpOpen, setHelpOpen] = useState(false);
  const [categories, setCategories] = useState(() => {
    try { const saved = JSON.parse(localStorage.getItem(CATEGORY_STORAGE_KEY) || "[]"); return Array.isArray(saved) ? saved : []; } catch { return []; }
  });
  const [categoryName, setCategoryName] = useState("");

  function addCategory(event) {
    event.preventDefault();
    const name = categoryName.trim();
    if (!name) return;
    if ([...categories, ...(report?.categorias_sugeridas || [])].some((category) => category.toLocaleLowerCase() === name.toLocaleLowerCase())) {
      setNotice({ type: "error", text: "Essa categoria já existe." });
      return;
    }
    const updated = [...categories, name];
    setCategories(updated);
    localStorage.setItem(CATEGORY_STORAGE_KEY, JSON.stringify(updated));
    setCategoryName("");
    setNotice({ type: "success", text: `Categoria “${name}” adicionada.` });
  }

  function goToMovements(event) {
    event.preventDefault();
    const target = document.getElementById(report ? "transacoes" : "importar");
    target?.scrollIntoView({ behavior: "smooth", block: "start" });
    if (!report) setNotice({ type: "success", text: "Importe um arquivo OFX para visualizar as movimentações." });
  }

  async function importFile(file) {
    if (!file) return;
    setBusy(true); setNotice(null);
    const data = new FormData(); data.append("file", file);
    try {
      const response = await fetch(`${API}/api/ofx/preview`, { method: "POST", body: data });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || "Não foi possível processar o arquivo.");
      setReport(result); setQuery(""); setFilter("Todas as categorias");
    } catch (error) { setNotice({ type: "error", text: error.message || "Não foi possível conectar à API." }); }
    finally { setBusy(false); if (inputRef.current) inputRef.current.value = ""; }
  }

  async function save() {
    if (!report) return;
    setSaving(true); setNotice(null);
    try {
      const response = await fetch(`${API}/api/ofx/save`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ movimentacoes: report.movimentacoes }) });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || "Falha ao salvar.");
      setNotice({ type: "success", text: "Extrato salvo com sucesso. Lançamentos repetidos foram ignorados." });
    } catch (error) { setNotice({ type: "error", text: error.message || "Não foi possível conectar à API." }); }
    finally { setSaving(false); }
  }

  async function exportMovements(format) {
    if (!rows.length) return;
    setExporting(format); setNotice(null);
    try {
      const response = await fetch(`${API}/api/ofx/export/${format}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ arquivo: report.arquivo, movimentacoes: rows }),
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Não foi possível gerar o arquivo.");
      }
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      const baseName = report.arquivo.replace(/\.ofx$/i, "").replace(/[^a-zA-Z0-9._ -]/g, "_");
      link.href = url;
      link.download = `${baseName || "movimentacoes"}-movimentacoes.${format === "excel" ? "xlsx" : format === "pdf" ? "pdf" : "csv"}`;
      document.body.appendChild(link); link.click(); link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (error) {
      setNotice({ type: "error", text: error.message || "Não foi possível conectar à API." });
    } finally { setExporting(null); }
  }

  async function checkBank() {
    setBank("checking");
    try { const response = await fetch(`${API}/api/health`); setBank(response.ok ? "online" : "offline"); }
    catch { setBank("offline"); }
  }

  const suggestedCategories = report?.categorias_sugeridas || [];
  const availableCategories = [...new Set([...suggestedCategories, ...categories])];
  const categoriesForFilter = ["Todas as categorias", "Sem categoria", ...availableCategories];
  function updateCategory(movimentacao, categoria) {
    const index = report.movimentacoes.indexOf(movimentacao);
    setReport((current) => ({ ...current, movimentacoes: current.movimentacoes.map((item, i) => i === index ? { ...item, categoria } : item) }));
  }
  const rows = (report?.movimentacoes || []).filter((m) => (filter === "Todas as categorias" || (filter === "Sem categoria" ? !m.categoria : m.categoria === filter)) && `${m.descricao} ${m.categoria}`.toLowerCase().includes(query.toLowerCase()));
  const uncategorizedCount = (report?.movimentacoes || []).filter((m) => !m.categoria?.trim()).length;

  return <div className="app-shell">
    <aside className="sidebar">
      <a className="brand" href="#inicio"><span className="brand-icon"><Landmark size={19}/></span><span>finança<span className="brand-dot">.</span><small>SEU ESPAÇO FINANCEIRO</small></span></a>
      <div className="side-label">MENU PRINCIPAL</div>
      <a className="nav-link active" href="#inicio"><Wallet size={18}/> Visão geral</a>
      <a className="nav-link" href="#transacoes" onClick={goToMovements}><ArrowDownLeft size={18}/> Movimentações</a>
      <div className="side-bottom"><div className="help-card"><div className="help-icon"><CircleHelp size={19}/></div><strong>Precisa de ajuda?</strong><p>Veja como importar seu extrato OFX.</p><a href="#ajuda" onClick={(event) => { event.preventDefault(); setHelpOpen(true); }}>Saiba mais <span>→</span></a></div><div className="profile"><div className="avatar">JC</div><div><strong>Meu espaço</strong><small>Controle financeiro</small></div><ChevronDown size={16}/></div></div>
    </aside>

    <main className="main" id="inicio">
      <header className="topbar"><div className="breadcrumb">Início <span>/</span> <strong>Visão geral</strong></div><div className="top-actions"><span className="secure"><ShieldCheck size={15}/> Seus dados protegidos</span><button className="icon-button" title="Ajuda"><CircleHelp size={19}/></button><div className="avatar small-avatar">JC</div></div></header>
      <div className="content">
        <div className="welcome-row" id="importar"><div><div className="eyebrow"><span className="sparkle"><Sparkles size={14}/></span> SEU RESUMO FINANCEIRO</div><h1>Visão geral</h1><p className="subtitle">Acompanhe suas movimentações em um só lugar.</p></div><button className="button button-primary" onClick={() => inputRef.current?.click()} disabled={busy}><Plus size={18}/>{busy ? "Lendo extrato..." : "Importar extrato"}</button><input ref={inputRef} type="file" accept=".ofx" hidden onChange={(e) => importFile(e.target.files?.[0])}/></div>

        {notice && <div className={`notice ${notice.type}`}><span>{notice.type === "success" ? <Check size={17}/> : <X size={17}/>}</span>{notice.text}<button onClick={() => setNotice(null)}><X size={16}/></button></div>}

        {report ? <>
          <section className="summary-grid">
            <article className="summary-card balance-card"><div className="card-top"><span className="card-icon mint"><Wallet size={18}/></span><span className="card-period">PERÍODO DO EXTRATO</span></div><div className="metric-label">Saldo do período</div><div className="metric-value">{brl(report.saldo)}</div><div className="metric-foot"><span className="dot-green"/> Atualizado agora</div><div className="balance-decoration"/></article>
            <article className="summary-card"><div className="card-top"><span className="card-icon green"><ArrowDownLeft size={18}/></span><span className="metric-tag positive">ENTRADAS</span></div><div className="metric-label">Total de entradas</div><div className="metric-value">{brl(report.entradas)}</div><div className="metric-foot">Valores recebidos no período</div></article>
            <article className="summary-card"><div className="card-top"><span className="card-icon coral"><ArrowUpRight size={18}/></span><span className="metric-tag negative">SAÍDAS</span></div><div className="metric-label">Total de saídas</div><div className="metric-value">{brl(Math.abs(report.saidas))}</div><div className="metric-foot">Valores pagos no período</div></article>
            <article className="summary-card"><div className="card-top"><span className="card-icon lavender"><FileUp size={18}/></span><span className="metric-tag neutral">MOVIMENTAÇÕES</span></div><div className="metric-label">Lançamentos encontrados</div><div className="metric-value">{report.quantidade}</div><div className="metric-foot">No arquivo {report.arquivo}</div></article>
          </section>

          <section className="transaction-panel" id="transacoes"><div className="panel-header"><div><h2>Movimentações</h2><p>Crie suas categorias e escolha uma para cada movimentação antes de salvar.</p></div><div className="panel-actions"><label className="search-box"><Search size={16}/><input placeholder="Buscar movimentação" value={query} onChange={(e) => setQuery(e.target.value)}/></label><label className="select-wrap"><select value={filter} onChange={(e) => setFilter(e.target.value)}>{categoriesForFilter.map((c) => <option key={c}>{c}</option>)}</select><ChevronDown size={15}/></label></div></div>
            <div className="category-manager"><div><strong>Sugestões deste extrato</strong><small>Você escolhe uma sugestão ou cria suas próprias categorias.</small></div><form onSubmit={addCategory}><input aria-label="Nome da nova categoria" placeholder="Ex.: Despesas fixas" value={categoryName} onChange={(event) => setCategoryName(event.target.value)} maxLength={40}/><button className="button button-category" type="submit" disabled={!categoryName.trim()}><Plus size={15}/> Adicionar</button></form>{(suggestedCategories.length > 0 || categories.length > 0) ? <div className="category-chips">{suggestedCategories.filter((category) => !categories.includes(category)).map((category) => <span className="suggested-category" key={`suggested-${category}`}>Sugestão: {category}</span>)}{categories.map((category) => <span key={`custom-${category}`}>{category}</span>)}</div> : <div className="category-empty">Nenhuma sugestão encontrada. Você pode criar suas próprias categorias.</div>}</div><div className="table-wrap"><table><thead><tr><th>DESCRIÇÃO</th><th>CATEGORIA</th><th>DATA</th><th className="align-right">VALOR</th></tr></thead><tbody>{rows.map((m, i) => <tr key={`${m.data}-${m.valor}-${i}`}><td><div className="transaction-name"><span className={`merchant-icon ${colors[m.categoria] || "gray"}`}>{m.valor >= 0 ? <ArrowDownLeft size={16}/> : <ArrowUpRight size={16}/>}</span><span><strong>{m.descricao}</strong><small>{m.valor >= 0 ? "Entrada" : "Saída"}</small></span></div></td><td><select aria-label={`Categoria de ${m.descricao}`} className={`category-edit ${colors[m.categoria] || "gray"}`} value={m.categoria || ""} onChange={(e) => updateCategory(m, e.target.value)}><option value="">Escolha uma categoria</option>{availableCategories.map((category) => <option key={category} value={category}>{category}</option>)}</select></td><td className="date-cell">{datePt(m.data)}</td><td className={`amount align-right ${m.valor >= 0 ? "amount-in" : ""}`}>{m.valor >= 0 ? "+ " : "− "}{brl(Math.abs(m.valor))}</td></tr>)}</tbody></table>{rows.length === 0 && <div className="empty-filter">Nenhuma movimentação encontrada.</div>}</div>
            <div className="table-footer"><span>Exibindo <strong>{rows.length}</strong> de <strong>{report.quantidade}</strong> movimentações{uncategorizedCount > 0 && <small className="uncategorized-note"> · {uncategorizedCount} sem categoria</small>}</span><div className="table-actions"><button className="button button-export" onClick={() => exportMovements("pdf")} disabled={exporting !== null || rows.length === 0}>{exporting === "pdf" ? <LoaderCircle className="spin" size={15}/> : <Download size={15}/>} PDF</button><button className="button button-export" onClick={() => exportMovements("excel")} disabled={exporting !== null || rows.length === 0}>{exporting === "excel" ? <LoaderCircle className="spin" size={15}/> : <Download size={15}/>} Excel</button><button className="button button-export" onClick={() => exportMovements("csv")} disabled={exporting !== null || rows.length === 0}>{exporting === "csv" ? <LoaderCircle className="spin" size={15}/> : <Download size={15}/>} CSV</button><button className="button button-save" onClick={save} disabled={saving || report.quantidade === 0 || uncategorizedCount > 0}>{saving ? <><LoaderCircle className="spin" size={16}/> Salvando...</> : <><Check size={16}/> Salvar no banco</>}</button></div></div>
          </section>
          <div className="file-strip"><span className="file-badge"><FileUp size={16}/></span><span><strong>{report.arquivo}</strong><small>Arquivo processado com sucesso</small></span><button onClick={() => setReport(null)} title="Remover extrato"><X size={16}/></button></div>
        </> : <>
          <section className="empty-layout"><div className="empty-copy"><span className="hero-kicker"><span/> ORGANIZE SUAS FINANÇAS</span><h2>Seu dinheiro,<br/><em>mais claro.</em></h2><p>Importe seu extrato bancário e veja suas entradas e saídas para classificar como preferir.</p><button className="button button-primary" onClick={() => inputRef.current?.click()} disabled={busy}><Upload size={17}/>{busy ? "Lendo extrato..." : "Escolher arquivo OFX"}</button><div className="format-note"><ShieldCheck size={15}/> Seus dados ficam protegidos e são enviados com segurança.</div></div><div className="upload-visual"><div className="orb orb-a"/><div className="orb orb-b"/><div className="float-card float-one"><span className="float-icon green"><ArrowDownLeft size={17}/></span><span><small>ENTRADA</small><strong>+ R$ 2.450,00</strong></span><span className="float-check"><Check size={13}/></span></div><div className="dashboard-card"><div className="mock-head"><span>Resumo financeiro</span><span className="mock-dots">•••</span></div><div className="mock-total">R$ 8.420,50</div><div className="mock-caption">Saldo do período <span>↗</span></div><div className="mock-chart"><div className="chart-grid"/><svg viewBox="0 0 420 120" preserveAspectRatio="none"><defs><linearGradient id="area" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stopColor="#71bd9b" stopOpacity=".24"/><stop offset="1" stopColor="#71bd9b" stopOpacity="0"/></linearGradient></defs><path d="M0 88 C32 83 35 55 69 61 S103 86 137 66 S179 51 204 61 S239 43 270 49 S302 72 333 37 S381 43 420 17 V120 H0Z" fill="url(#area)"/><path d="M0 88 C32 83 35 55 69 61 S103 86 137 66 S179 51 204 61 S239 43 270 49 S302 72 333 37 S381 43 420 17" fill="none" stroke="#56a985" strokeWidth="3" strokeLinecap="round"/></svg></div><div className="mock-legend"><span><i className="legend-green"/>Entradas</span><span><i className="legend-coral"/>Saídas</span><span>Últimos 30 dias</span></div></div><div className="float-card float-two"><span className="float-icon peach"><Sparkles size={17}/></span><span><small>CATEGORIA</small><strong>Categoria criada</strong></span><span className="float-check"><Check size={13}/></span></div><div className="upload-hint"><span><FileUp size={17}/></span>Extrato importado<small>OFX · pronto para analisar</small></div></div></section>
          <section className="steps" id="ajuda"><div className="steps-heading"><span>É simples assim</span><small>SEU CONTROLE, SEM COMPLICAÇÃO</small></div><div className="step-item"><span className="step-number">01</span><div><strong>Envie seu extrato</strong><p>Selecione o arquivo OFX do seu banco.</p></div></div><div className="step-item"><span className="step-number">02</span><div><strong>Confira os detalhes</strong><p>Veja valores e categorias organizados.</p></div></div><div className="step-item"><span className="step-number">03</span><div><strong>Salve com segurança</strong><p>Guarde os lançamentos no seu banco.</p></div></div></section>
        </>}
        {helpOpen && <div className="construction-overlay" role="dialog" aria-modal="true" aria-labelledby="construction-title"><section className="construction-card"><button className="construction-close" onClick={() => setHelpOpen(false)} aria-label="Fechar"><X size={18}/></button><span className="construction-icon"><CircleHelp size={28}/></span><span className="construction-badge">EM CONSTRUÇÃO</span><h2 id="construction-title">Central de ajuda</h2><p>Estamos preparando orientações para importar extratos, revisar categorias e exportar movimentações.</p><div className="construction-progress"><span/></div><small>Esta área estará disponível em breve.</small><button className="button button-primary" onClick={() => setHelpOpen(false)}>Voltar para o painel</button></section></div>}
        <footer className="footer"><span>© 2026 Projeto OFX</span><span className={`connection ${bank}`}><i/>{bank === "online" ? "Banco conectado" : bank === "offline" ? "Banco desconectado" : ""}<button onClick={checkBank}>{bank === "idle" ? "Verificar conexão" : bank === "checking" ? "Verificando..." : "Verificar novamente"}</button></span></footer>
      </div>
    </main>
  </div>;
}

















