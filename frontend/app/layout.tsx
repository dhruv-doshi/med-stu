import "./globals.css";

export const metadata = { title: "AI Virtual Patient Simulator", description: "Educational clinical simulation" };
export default function Layout({ children }: Readonly<{ children: React.ReactNode }>) { return <html lang="en"><body>{children}</body></html>; }
