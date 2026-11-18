"use client";
import { useEffect, useState } from "react";

export function useData(name) {
  const [rows, setRows] = useState(null);
  useEffect(() => {
    fetch(`/data/${name}.json`)
      .then((r) => (r.ok ? r.json() : []))
      .then((d) => setRows(Array.isArray(d) ? d : []))
      .catch(() => setRows([]));
  }, [name]);
  return rows;
}

export const num = (v) => Number(v ?? 0);
export const usd = (v) => (v == null ? "-" : "$" + num(v).toLocaleString("en-US", { maximumFractionDigits: 0 }));
export const ratio = (v) => (v == null ? "-" : num(v).toFixed(2));
export const day = (v) => String(v ?? "").slice(0, 10);
