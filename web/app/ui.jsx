export function Section({ title, note, rows, children }) {
  return (
    <section>
      <h2>{title}</h2>
      {note && <p className="note">{note}</p>}
      {rows === null ? (
        <p className="empty">Loading...</p>
      ) : rows.length === 0 ? (
        <p className="empty">No data yet. Copy the exported JSON into public/data.</p>
      ) : (
        children
      )}
    </section>
  );
}

export function Table({ cols, rows }) {
  return (
    <div className="scroll">
      <table>
        <thead>
          <tr>{cols.map(([label]) => <th key={label}>{label}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i}>
              {cols.map(([label, key, fmt]) => <td key={label}>{fmt ? fmt(r[key]) : String(r[key] ?? "")}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
