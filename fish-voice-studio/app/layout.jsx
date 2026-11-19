import "./globals.css";

export const metadata = {
  title: "Farhan Voice Studio",
  description: "Fish Audio powered text to speech studio",
};

export default function RootLayout({ children }) {
  return <html lang="en"><body>{children}</body></html>;
}
