const STEPS = [
  {
    idx: 'Manifest',
    title: 'Read the declaration',
    body: 'We parse the APK\u2019s manifest and pull every permission it declares, along with basic app metadata.',
  },
  {
    idx: 'Context',
    title: 'Check it against purpose',
    body: 'Each permission is compared with what the app claims to do \u2014 the same permission can be expected in one app and unusual in another.',
  },
  {
    idx: 'Evidence',
    title: 'Look for supporting signals',
    body: 'Where possible, we check for API references that back up a permission \u2014 stronger evidence than the permission alone.',
  },
  {
    idx: 'Verdict',
    title: 'Score and explain',
    body: 'Everything rolls up into a risk score and a plain-language explanation you don\u2019t need a security background to read.',
  },
]

export default function HowItWorks() {
  return (
    <section className="how" id="how-it-works">
      <div className="wrap">
        <h2>How the inspection works</h2>
        <div className="how-grid">
          {STEPS.map((s) => (
            <div className="how-cell" key={s.idx}>
              <div className="idx">{s.idx}</div>
              <h3>{s.title}</h3>
              <p>{s.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}