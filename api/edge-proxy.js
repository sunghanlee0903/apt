// Vercel Edge Function - runs on Cloudflare global edge (Seoul PoP for Korean users)
// This bypasses the US serverless IP block from data.go.kr
export const config = { runtime: 'edge' };

export default async function handler(req) {
  const url = new URL(req.url);
  const sigunguCode = url.searchParams.get('sigungu_code');
  const yearMonth = url.searchParams.get('year_month');

  if (!sigunguCode || !yearMonth) {
    return new Response(JSON.stringify({ error: 'sigungu_code and year_month are required' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
    });
  }

  const apiKey = process.env.APT_KEY || '';
  if (!apiKey) {
    return new Response(JSON.stringify({ error: 'APT_KEY not configured' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
    });
  }

  const apiUrl = new URL(
    'https://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade'
  );
  apiUrl.searchParams.set('serviceKey', apiKey);
  apiUrl.searchParams.set('LAWD_CD', sigunguCode);
  apiUrl.searchParams.set('DEAL_YMD', yearMonth);
  apiUrl.searchParams.set('numOfRows', '500');
  apiUrl.searchParams.set('pageNo', '1');

  try {
    const govRes = await fetch(apiUrl.toString(), {
      signal: AbortSignal.timeout(8000),
    });

    const xmlText = await govRes.text();

    if (govRes.status === 403) {
      return new Response(
        JSON.stringify({ status: 'error', source: 'edge_block', message: '403 - IP blocked even from edge' }),
        {
          status: 403,
          headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
        }
      );
    }

    return new Response(xmlText, {
      status: 200,
      headers: {
        'Content-Type': 'application/xml; charset=utf-8',
        'Access-Control-Allow-Origin': '*',
      },
    });
  } catch (err) {
    return new Response(
      JSON.stringify({ status: 'error', message: err.message }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
      }
    );
  }
}
