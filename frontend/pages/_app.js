/*
 * Next.js app component.
 * Wraps all pages with global styles.
 */

import '../styles/globals.css'

function MyApp({ Component, pageProps }) {
  // Render the current page component with props
  return <Component {...pageProps} />
}

export default MyApp