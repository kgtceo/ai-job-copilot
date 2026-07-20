import type { Metadata } from "next";
import "./globals.css";

const url = "https://aicopilot.kareemghazal.com";
const title = "AI Job Copilot — CV-to-job tailoring, measured";
const description =
  "A grounded LLM pipeline that tailors your CV to a job description via structured output — with a real eval harness (deterministic checks + LLM-as-judge). Live + open-source.";

export const metadata: Metadata = {
  metadataBase: new URL(url),
  title,
  description,
  alternates: { canonical: "/" },
  openGraph: {
    type: "website",
    url,
    siteName: "AI Job Copilot",
    title,
    description,
    locale: "en_GB",
    images: [
      {
        url: "/og.jpg",
        width: 1200,
        height: 630,
        alt: "AI Job Copilot — a CV-to-job tailoring pipeline with an eval harness",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title,
    description,
    images: ["/og.jpg"],
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
