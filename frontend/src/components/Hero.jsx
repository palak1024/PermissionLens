export default function Hero() {
  return (
    <section className="hero">
      <div className="wrap">
        <div className="hero-eyebrow">Android permission &amp; risk analysis</div>
        <h1>
          A calculator app asking for your <em>microphone</em> isn't a bug report. It's a question nobody's asking.
        </h1>
        <p className="lede">
          PermissionLens reads an APK's declared permissions the way a customs officer reads a
          declaration form — not just what's on the list, but whether it makes sense for what
          the app claims to be. Upload one below and see the manifest for yourself.
        </p>
        <div className="hero-stats">
          <div className="hero-stat">
            <b>15+</b>
            <span>Permissions classified</span>
          </div>
          <div className="hero-stat">
            <b>4</b>
            <span>Risk levels</span>
          </div>
          <div className="hero-stat">
            <b>Static</b>
            <span>Analysis, no install needed</span>
          </div>
        </div>
      </div>
    </section>
  )
}