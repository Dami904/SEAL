import type { Metadata } from "next";
import { DM_Sans, Geist_Mono } from "next/font/google";
import { Nav } from "@/components/layout/Nav";
import "./globals.css";

const dmSans = DM_Sans({ subsets: ["latin"], variable: "--font-dm-sans" });
const geistMono = Geist_Mono({ subsets: ["latin"], variable: "--font-geist-mono" });

export const metadata: Metadata = {
  title: "SEAL — Bitget Alpha Factory",
  description:
    "Trade Bitget rTokens when US cash stocks are closed. Publish the rule. Seal the size.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${dmSans.variable} ${geistMono.variable}`}>
      <body>
        <Nav />
        <main className="mx-auto max-w-desk px-4 py-10 sm:px-6">{children}</main>
      </body>
    </html>
  );
}
