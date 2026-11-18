import { REPO_URL } from "./config";

export default function Home() {
  return (
    <>
      <h1>Data Analytics Portfolio</h1>
      <p className="note">Two projects built for the Nexvia data analytics track. Source code and setup steps are in the <a href={REPO_URL}>GitHub repository</a>.</p>
      <div className="cards">
        <a className="card" href="/customer-360">
          <b>Customer 360 and Marketing Attribution</b>
          <span>Which channels bring revenue: four attribution models, ROI, RFM segments.</span>
        </a>
        <a className="card" href="/control-tower">
          <b>Retail and Supply Chain Control Tower</b>
          <span>Stock, delivery and supplier monitoring with anomaly alerts and a what-if panel.</span>
        </a>
      </div>
    </>
  );
}
