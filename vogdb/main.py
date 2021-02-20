import contextlib

from slowapi.errors import RateLimitExceeded
from starlette.requests import Request

from .functionality import *
from .database import SessionLocal
from sqlalchemy.orm import Session
from fastapi import Depends, FastAPI, Query, Path, HTTPException
from fastapi.responses import PlainTextResponse
from .schemas import *
import logging
from .models import Species
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

# configuring logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(module)s- %(funcName)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

# get logger:
log = logging.getLogger(__name__)

api = FastAPI()

# request limiter
limiter = Limiter(key_func=get_remote_address)
api.state.limiter = limiter
api.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@contextlib.contextmanager
def error_handling():
    try:
        yield
    except HTTPException:
        raise
    except (ValueError, KeyError, AttributeError) as e:
        log.exception("Bad request")
        raise HTTPException(400, str(e)) from e
    except Exception as e:
        log.exception("Internal server error")
        raise HTTPException(500, str(e)) from e


# uncomment when we have a domain
# redirected_app = HTTPToHTTPSRedirectMiddleware(api, host="example_domain.com")


# Dependency. Connect to the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@api.get("/", summary="Welcome", response_model=WELCOME)
async def root(db: Session = Depends(get_db)):
    query = db.query(Species.version).first()
    version = query[0]
    log.debug(f"Fileshare-Version: {version}")
    return WELCOME(message="Welcome to the VOGDB-API.", version=version)


@api.get("/vsearch/species",
         response_class=PlainTextResponse, summary="Species search")
@limiter.limit("9/second")
async def search_species(
        request: Request,
        db: Session = Depends(get_db),
        taxon_id: List[int] = Query(None, title="Taxon ID", le=9999999, description="Species identity number",
                                    example={"2713301"}),
        name: List[str] = Query(None, max_length=20, title="species name",
                                description="species name", example={"corona"}),
        phage: Optional[bool] = Query(None, example="True"),
        source: Optional[str] = Query(None, max_length=20, regex="^[a-zA-Z\s]*$", example="NCBI")):
    """
    This functions searches a database and returns a list of species IDs for records in that database
    which meet the search criteria.
    \f
    :return: A List of Species IDs
    """
    if all(param is None for param in [name, taxon_id, phage, source]):
        raise HTTPException(status_code=400, detail="No parameters given.")
    with error_handling():
        log.debug("Received a vsearch/species request")

        species_list = [str(i[0]) for i in get_species(db, taxon_id, name, phage, source)]

        species = PlainTextResponse('\n'.join(species_list))

        if not species.body.decode("utf-8"):
            log.info("No Species match the search criteria.")

        else:
            log.info("Species have been retrieved.")

        return species


@api.get("/vsummary/species",
         response_model=List[Species_profile], summary="Species summary")
@limiter.limit("9/second")
async def get_summary_species(request: Request,
                              taxon_id: Optional[List[int]] = Query(..., title="Taxon ID", le=9999999,
                                                                    description="Species identity number",
                                                                    example={"2713301"}),
                              db: Session = Depends(get_db)):
    """
    This function returns Species summaries for a list of taxon ids.
    \f
    :param taxon_id: Taxon ID
    :param db: database session dependency
    :return: Species summary
    """

    with error_handling():
        log.debug("Received a vsummary/species GET with parameters: taxon_id = {0}".format(taxon_id))

        species_summary = find_species_by_id(db, taxon_id)

        if not len(species_summary) == len(taxon_id):
            log.warning("At least one of the species was not found, or there were duplicates.\n"
                        "IDs given: {0}".format(taxon_id))

        if not species_summary:
            log.debug("No matching Species found")
            raise HTTPException(status_code=404, detail="Item not found")
        else:
            log.info("Species summaries have been retrieved.")

        return species_summary


@api.post("/vsummary/species",
          response_model=List[Species_profile], summary="Species summary")
async def post_summary_species(body: List[Species_ID], db: Session = Depends(get_db)):
    """
    This function returns Species summaries for a list of taxon ids.
    \f
    :param body: Taxon ID
    :param db: database session dependency
    :return: Species summary
    """
    return await get_summary_species([s.taxon_id for s in body], db)


@api.get("/vsearch/vog",
         response_class=PlainTextResponse, summary="VOG search")
@limiter.limit("9/second")
async def search_vog(
        request: Request,
        id: Optional[Set[str]] = Query(None, max_length=10, regex="^VOG", title="VOG ID",
                                       description="VOG identity number", example={"VOG00004"}),
        pmin: Optional[int] = Query(None, ge=0, le=999999, title="protein max limit",
                                    description="maximum number of proteins for a VOG", example=66),
        pmax: Optional[int] = Query(None, ge=0, le=999999, title="protein min limit",
                                    description="minimum number of proteins for a VOG", example=5),
        smax: Optional[int] = Query(None, ge=0, le=999999, title="species max limit",
                                    description="maximum number of species for a VOG", example=66),
        smin: Optional[int] = Query(None, ge=0, le=999999, title="species max limit",
                                    description="maximum number of species for a VOG", example=5),
        functional_category: Optional[Set[str]] = Query(None, max_length=5, title="functional categories",
                                                        description="[Xr] Virus replication, [Xs] Virus structure; " +
                                                                    "[Xh] [Xp] protein function beneficial for the host, virus, respectively; " +
                                                                    "[Xu] unknown function", example={"XrXs"}),
        consensus_function: Optional[Set[str]] = Query(None, max_length=100, title="consensus function",
                                                       description="consensus function of the protein",
                                                       example={"Transcriptional activator"}),
        mingLCA: Optional[int] = Query(None, ge=0, le=999999, title="gLCA min limit",
                                       description="minimal number of genomes in LCA", example=2000),
        maxgLCA: Optional[int] = Query(None, ge=0, le=999999, title="gLCA max limit",
                                       description="maximal number of genomes in group and LCA", example=10000),
        mingGLCA: Optional[int] = Query(None, ge=0, le=999999, title="gGLCA min limit",
                                        description="minimal number of genomes in group and LCA", example=2000),
        maxgGLCA: Optional[int] = Query(None, ge=0, le=999999, title="gGLCA min limit",
                                        description="minimal number of genomes in LCA", example=2000),
        ancestors: Optional[Set[str]] = Query(None, max_length=200, title="last common ancestors",
                                              example={"Viruses;Varidnaviria"}),
        h_stringency: Optional[bool] = Query(None, title="high virus stringency"),
        m_stringency: Optional[bool] = Query(None, title="medium virus stringency"),
        l_stringency: Optional[bool] = Query(None, title="low virus stringency"),
        virus_specific: Optional[bool] = Query(None),
        phages_nonphages: Optional[str] = Query(None, max_length=20, title="select only phage/nonphage VOGs",
                                                example="phages"),
        proteins: Optional[Set[str]] = Query(None, regex="^.*(YP|NP).*$", title="Protein ID",
                                             description="Protein taxon identity number",
                                             example={"2301601.YP_009812740.1"}),
        species: Optional[Set[str]] = Query(None, max_length=20, regex="^[a-zA-Z\s]*$", title="species name",
                                            description="species name", example={"bovine coronavirus"}),
        tax_id: Optional[Set[int]] = Query(None, title="Taxon ID", le=9999999,
                                           description="Species identity number", example={"2713301"}),
        union: Optional[bool] = Query(None, title="union boolean",
                                      description="When at least two taxonomy IDs or species names are provided,"
                                                  " the VOGs containing either are returned, when the union parameter is set to True. Otherwise the result is"
                                                  " the intersection of the VOGs contained in either group."),
        db: Session = Depends(get_db)):
    """
    This functions searches a database and returns a list of vog unique identifiers (UIDs) for records in that database
    which meet the search criteria.
    \f
    :return: A List of VOG IDs
    """

    if all(param is None for param in [id, pmin, pmax, smin, smax, union, tax_id, species, proteins, phages_nonphages,
                                       virus_specific, l_stringency, m_stringency, h_stringency, ancestors, maxgLCA,
                                       maxgGLCA, mingGLCA, mingLCA, consensus_function, functional_category]):
        raise HTTPException(status_code=400, detail="No parameters given.")

    with error_handling():
        log.debug("Received a vsearch/vog request")

        vog_list = [str(i[0]) for i in get_vogs(db, id, pmin, pmax, smax, smin, functional_category, consensus_function,
                                                mingLCA, maxgLCA, mingGLCA, maxgGLCA, ancestors, h_stringency,
                                                m_stringency, l_stringency,
                                                virus_specific, phages_nonphages, proteins, species, tax_id, union)]

        vogs = PlainTextResponse('\n'.join(vog_list))

        if not vogs.body.decode("utf-8"):
            log.info("No VOGs match the search criteria.")

        else:
            log.info("VOGs have been retrieved.")

        return vogs


@api.get("/vsummary/vog", response_model=List[VOG_profile], summary="VOG summary")
@limiter.limit("9/second")
async def get_summary_vog(request: Request, id: List[str] = Query(..., max_length=10, regex="^VOG", title="VOG ID",
                                                                  description="VOG identity number",
                                                                  example={"VOG00004"}),
                          db: Session = Depends(get_db)):
    """
    This function returns vog summaries for a list of unique identifiers (UIDs).
    \f
    :param id: VOGID
    :param db: database session dependency
    :return: vog summary
    """

    with error_handling():
        log.debug("Received a vsummary/vog request")

        vog_summary = find_vogs_by_uid(db, id)

        if not vog_summary:
            log.debug("No matching VOGs found")
            raise HTTPException(status_code=404, detail="Item not found")
        else:
            log.debug("VOG summaries have been retrieved.")

        return vog_summary


@api.post("/vsummary/vog",
          response_model=List[VOG_profile], summary="VOG summary")
async def post_summary_species(body: List[VOG_UID], db: Session = Depends(get_db)):
    """
    This function returns Species summaries for a list of taxon ids.
    \f
    :param body: list of VOG uids as returned from search_vog
    :param db: database session dependency
    :return: VOG summary object
    """
    return await get_summary_vog([vog.id for vog in body], db)


@api.get("/vfetch/vog/hmm", response_model=Dict[str, str], summary="VOG HMM fetch")
@limiter.limit("9/second")
async def get_fetch_vog_hmm(request: Request, id: List[str] = Query(..., max_length=10, regex="^VOG", title="VOG ID",
                                                                    description="VOG identity number",
                                                                    example={"VOG00004"})):
    """
    This function returns the Hidden Markov Matrix (HMM) for a list of unique identifiers (UIDs)
    \f
    :param id: VOGID
    :return: vog data (HMM profile)
    """
    with error_handling():
        log.debug("Received a vfetch/vog/hmm request")

        vog_hmm = find_vogs_hmm_by_uid(id)

        if len(vog_hmm) == 0:
            log.debug("No HMM found.")
            raise HTTPException(status_code=404, detail="Item not found")

        log.debug("HMM search successful.")
        return vog_hmm


@api.post("/vfetch/vog/hmm", response_model=Dict[str, str], summary="VOG HMM fetch")
async def post_fetch_vog_hmm(body: List[VOG_UID]):
    """
    This function returns the Hidden Markov Matrix (HMM) for a list of unique identifiers (UIDs)
    \f
    :param body: list of VOG uids as returned from search_vog
    :return: vog data (HMM profile)
    """
    return await get_fetch_vog_hmm([vog.id for vog in body])


@api.get("/vfetch/vog/msa", response_model=Dict[str, str], summary="VOG MSA fetch")
@limiter.limit("9/second")
async def get_fetch_vog_msa(request: Request, id: List[str] = Query(..., max_length=10, regex="^VOG", title="VOG ID",
                                                                    description="VOG identity number",
                                                                    example={"VOG00004"})):
    """
    This function returns the Multiple Sequence Alignment (MSA) for a list of unique identifiers (UIDs)
    \f
    :param id: VOGID
    :return: vog data (MSA)
    """
    with error_handling():
        log.debug("Received a vfetch/vog/msa request")
        vog_msa = find_vogs_msa_by_uid(id)

        if len(vog_msa) == 0:
            log.debug("No MSA found.")
            raise HTTPException(status_code=404, detail="Item not found")

        log.debug("MSA search successful.")

        return vog_msa


@api.post("/vfetch/vog/msa", response_model=Dict[str, str], summary="VOG MSA fetch")
async def post_fetch_vog_msa(body: List[VOG_UID]):
    """
    This function returns the Multiple Sequence Alignment (MSA) for VOGs
    \f
    :param body: list of VOG uids as returned from search_vog
    :return: vog data (HMM profile)
    """
    return await get_fetch_vog_msa([vog.id for vog in body])


@api.get("/vplain/vog/hmm/{id}", response_class=PlainTextResponse, summary="VOG HMM fetch plain text")
async def plain_vog_hmm(id: str = Path(..., title="VOG id", min_length=8, regex="^VOG\d+$")):
    """
    Get the Hidden Markov Matrix of the given VOG as plain text.
    \f
    :param id: VOGID
    """

    with error_handling():
        try:
            return PlainTextResponse(hmm_content(id))
        except KeyError:
            raise HTTPException(404, "Not found")


@api.get("/vplain/vog/msa/{id}", response_class=PlainTextResponse, summary="VOG MSA fetch plain text")
async def plain_vog_msa(id: str = Path(..., title="VOG id", min_length=8, regex="^VOG\d+$")):
    """
    Get the Multiple Sequence Alignment of the given VOG as plain text.
    \f
    :param id: VOGID
    """

    with error_handling():
        try:
            return PlainTextResponse(msa_content(id))
        except KeyError:
            raise HTTPException(404, "Not found")


@api.get("/vsearch/protein",
         response_class=PlainTextResponse, summary="Protein search")
@limiter.limit("9/second")
async def search_protein(request: Request,
                         species_name: List[str] = Query(None, max_length=20, regex="^[a-zA-Z\s]*$",
                                                         title="species name",
                                                         description="species name", example={"corona"}),
                         taxon_id: List[int] = Query(None, title="Taxon ID", le=9999999,
                                                     description="Species identity number", example={"2713301"}),
                         VOG_id: List[str] = Query(None, max_length=10, regex="^VOG", title="VOG ID",
                                                   description="VOG identity number", example={"VOG00004"}),
                         db: Session = Depends(get_db)):
    """
    This functions searches a database and returns a list of Protein IDs for records in the database
    matching the search criteria.
    \f
    :param: species_name: full or partial name of a species
    :param: taxon_id: Taxnonomy ID of a species
    :param: VOG_id: ID of the VOG(s)
    :return: A List of Protein IDs
    """
    if all(param is None for param in [species_name, taxon_id, VOG_id]):
        raise HTTPException(status_code=400, detail="No parameters given.")

    with error_handling():
        log.debug("Received a vsearch/protein request")

        protein_list = [str(i[0]) for i in get_proteins(db, species_name, taxon_id, VOG_id)]

        proteins = PlainTextResponse('\n'.join(protein_list))

        if not proteins.body.decode("utf-8"):
            log.debug("No Proteins match the search criteria.")
        else:
            log.debug("Proteins have been retrieved.")

        return proteins


@api.get("/vsummary/protein",
         response_model=List[Protein_profile], summary="Protein summary")
@limiter.limit("9/second")
async def get_summary_protein(request: Request,
                              id: List[str] = Query(..., max_length=25, regex="^.*(YP|NP).*$", title="Protein ID",
                                                    description="Protein taxon identity number",
                                                    example={"2301601.YP_009812740.1"}),
                              db: Session = Depends(get_db)):
    """
    This function returns protein summaries for a list of Protein identifiers (pids)
    \f
    :param id: proteinID
    :param db: database session dependency
    :return: protein summary
    """
    with error_handling():
        log.debug("Received a vsummary/protein request")

        protein_summary = find_proteins_by_id(db, id)

        if not len(protein_summary) == len(id):
            log.warning("At least one of the proteins was not found, or there were duplicates.\n"
                        "IDs given: {0}".format(id))

        if not protein_summary:
            log.debug("No matching Proteins found")
            raise HTTPException(status_code=404, detail="Item not found")
        else:
            log.debug("Protein summaries have been retrieved.")

        return protein_summary


@api.post("/vsummary/protein", response_model=List[Protein_profile], summary="Protein summary")
async def post_summary_protein(body: List[ProteinID], db: Session = Depends(get_db)):
    """
    This function returns protein summaries for a list of Protein identifiers (pids)
    \f
    :param body: proteinIDs as returned from search_protein
    :param db: database session dependency
    :return: list of protein summaries
    """
    return await get_summary_protein([p.id for p in body], db)


@api.get("/vfetch/protein/faa",
         response_model=List[AA_seq], summary="Protein AA fetch")
@limiter.limit("9/second")
async def get_fetch_protein_faa(request: Request,
                                id: List[str] = Query(..., max_length=25, regex="^.*(YP|NP).*$", title="Protein ID",
                                                      description="Protein taxon identity number",
                                                      example={"2301601.YP_009812740.1"}),
                                db: Session = Depends(get_db)):
    """
    This function returns Amino acid sequences for the proteins specified by the protein IDs
    \f
    :param id: ProteinID(s)
    :param db: database session dependency
    :return: Amino acid sequences for the proteins
    """
    with error_handling():
        log.debug("Received a vfetch/protein/faa request")
        protein_faa = find_protein_faa_by_id(db, id)
        if not len(protein_faa) == len(id):
            log.warning("At least one of the proteins was not found, or there were duplicates.\n"
                        "IDs given: {0}".format(id))

        if not protein_faa:
            log.debug("No Proteins found with the given IDs")
            raise HTTPException(status_code=404, detail="Item not found")
        else:
            log.debug("Aminoacid sequences have been retrieved.")

        return protein_faa


@api.post("/vfetch/protein/faa", response_model=List[AA_seq], summary="Protein AA fetch")
async def post_fetch_protein_faa(body: List[ProteinID], db: Session = Depends(get_db)):
    """
    This function returns Amino acid sequences for the proteins specified by the protein IDs
    \f
    :param body: proteinIDs as returned from search_protein
    :param db: database session dependency
    :return: Amino acid sequences for the proteins
    """
    return await get_fetch_protein_faa([p.id for p in body], db)


@api.get("/vfetch/protein/fna",
         response_model=List[NT_seq], summary="Protein NT fetch")
@limiter.limit("9/second")
async def get_fetch_protein_fna(request: Request,
                                id: List[str] = Query(..., max_length=25, regex="^.*(YP|NP).*$", title="Protein ID",
                                                      description="Protein taxon identity number",
                                                      example={"2301601.YP_009812740.1"}),
                                db: Session = Depends(get_db)):
    """
    This function returns Nucleotide sequences for the genes specified by the protein IDs
    \f
    :param id: ProteinID(s)
    :param db: database session dependency
    :return: Nucleotide sequences for the proteins
    """
    with error_handling():
        log.debug("Received a vfetch/protein/fna request")

        protein_fna = find_protein_fna_by_id(db, id)

        if not len(protein_fna) == len(id):
            log.warning("At least one of the proteins was not found, or there were duplicates.\n"
                        "IDs given: {0}".format(id))

        if not protein_fna:
            log.debug("No Proteins found with the given IDs")
            raise HTTPException(status_code=404, detail="Item not found")
        else:
            log.debug("Nucleotide sequences have been retrieved.")

        return protein_fna


@api.post("/vfetch/protein/fna", response_model=List[NT_seq], summary="Protein NT fetch")
async def post_fetch_protein_fna(body: List[ProteinID], db: Session = Depends(get_db)):
    """
    This function returns Nucleotide sequences for the genes specified by the protein IDs
    \f
    :param body: proteinIDs as returned from search_protein
    :param db: database session dependency
    :return: Nucleotide sequences for the proteins
    """
    return await get_fetch_protein_fna([p.id for p in body], db)
