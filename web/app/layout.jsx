import "./globals.css";
import { REPO_URL } from "./config";

export const metadata = { title: "Data Analytics Portfolio" };

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <nav>
          <a href="/">Home</a>
          <a href="/customer-360">Customer 360</a>
          <a href="/control-tower">Control Tower</a>
          <a href={REPO_URL}>GitHub</a>
        </nav>
        <main>{children}</main>
      </body>
    </html>
  );
}
