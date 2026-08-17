const LEVEL_LABEL = {
  low: 'Low risk',
  medium: 'Medium risk',
  high: 'High risk',
  critical: 'Critical risk',
}

const STATUS_LABEL = {
  ok: 'Expected',
  warn: 'Unusual',
  danger: 'High concern',
}

export default function ReportCard({ report, onReset }) {
  const {
    appName,
    packageName,
    category,
    score,
    level,
    permissions,
    evidence,
    explanation,
    recommendations,
    source,
  } = report

  return (
    <div className="report">
      <div className="report-head">
        <div className="report-head-left">
          <div className="eyebrow">Inspection report</div>
          <h3>{appName || 'Unnamed application'}</h3>
          <div className="pkg">{packageName} &middot; categorized as {category}</div>
        </div>
        <div className={`stamp ${level}`} data-score={`${score} / 100`}>
          {LEVEL_LABEL[level] || 'Reviewed'}
        </div>
      </div>

      <div className="report-body">
        <div className="report-section">
          <h4>Permission manifest</h4>
          <div className="manifest">
            {permissions.map((p) => (
              <div className="manifest-row" key={p.code}>
                <span className={`tag ${p.status}`}>{STATUS_LABEL[p.status]}</span>
                <span>
                  <span className="manifest-name">{p.label}</span>
                  <span className="manifest-note">{p.code}</span>
                </span>
              </div>
            ))}
          </div>
        </div>

        {evidence?.length > 0 && (
          <div className="report-section">
            <h4>Supporting evidence</h4>
            <div className="evidence-list">
              {evidence.map((e, i) => (
                <div className="evidence-item" key={i}>
                  <span className="dot" aria-hidden="true" />
                  <span>{e}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="report-section">
          <h4>What this means</h4>
          <div className="explanation-box">{explanation}</div>
        </div>

        <div className="report-section">
          <h4>Recommended next steps</h4>
          <ol className="recs">
            {recommendations.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ol>
        </div>
      </div>

      <div className="report-footer">
        <span className="disclaimer">
          A risk indicator based on static analysis, not proof of malicious behavior.
          {source === 'local-demo' && ' Demo mode \u2014 connect the FastAPI backend for live analysis.'}
        </span>
        <button type="button" className="rescan-btn" onClick={onReset}>
          Inspect another APK
        </button>
      </div>
    </div>
  )
}