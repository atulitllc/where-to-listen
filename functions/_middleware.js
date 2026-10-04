// www → https apex, preserving path and query.
// Matches wheretowatchfree.com (functions/_middleware.js). _redirects cannot match a hostname.
const APEX = "findthispodcast.com";

export async function onRequest(context) {
  const url = new URL(context.request.url);
  if (url.hostname.toLowerCase() === "www." + APEX) {
    url.hostname = APEX;
    url.protocol = "https:";
    return Response.redirect(url.toString(), 301);
  }
  return context.next();
}
