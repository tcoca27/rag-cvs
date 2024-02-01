'use client'

import {Input, Textarea} from "@nextui-org/input";
import {useEffect, useRef, useState} from "react";
import {Accordion, AccordionItem, Button, Spinner} from "@nextui-org/react";
import {Modal, ModalBody, ModalContent, ModalHeader} from "@nextui-org/modal";
import UploadPhoto from "@/components/icons/UploadPhoto";

const ResumeMatcher = () => {
    const [jobDescription, setJobDescription] = useState("");
    const [numberToRetrieve, setNumberToRetrieve] = useState(5);
    const [resumes, setResumes] = useState([]);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const fileInputRef = useRef(null);
    const [indexedFiles, setIndexedFiles] = useState([]);
    const [toIndex, setToIndex] = useState([]);
    const [isLoading, setLoading] = useState(true);
    const [modalDescription, setModalDescription] = useState("");
    const [githubs, setGithubs] = useState([]);

    useEffect(() => {
        getFilesStatus();
    }, [])


    const getFilesStatus = async () => {
        setLoading(true);
        const response = await fetch('http://127.0.0.1:8000/api/resume/files', {
            method: 'GET'
        });
        const body = await response.json();
        setIndexedFiles(body.indexed);
        setToIndex(body.not_indexed);
        setLoading(false);
    }

    const retrieve = async (type: string) => {
        setModalDescription("Matching Resumes");
        setIsModalOpen(true);
        const response = await fetch(`/api/resume`, {
            method: 'POST',
            headers: {
                "Content-type": "application/json",
            },
            body: JSON.stringify({
                type: type,
                jobDescription,
                topK: numberToRetrieve
            })
        });
        const body = await response.json();
        setResumes(body);
        setIsModalOpen(false);
    }

    const handleFileUpload = async (event) => {
        const files = event.target.files;
        const formData = new FormData();
        for (const file of files) {
            formData.append('files', file);
        }

        const uploadUrl = 'http://127.0.0.1:8000/api/resume/upload';

        try {
            const response = await fetch(uploadUrl, {
                method: 'POST',
                body: formData,
                headers: {
                    ContentType: 'multipart/form-data'
                }
            });

            if (response.ok) {
                getFilesStatus();
            } else {
                console.error('Upload failed', response.statusText);
            }
        } catch (error) {
            console.error('Error during file upload', error);
        }
    };

    const startIndex = async () => {
        setModalDescription("Indexing. This might take a while...");
        setIsModalOpen(true)
        const response = await fetch('http://127.0.0.1:8000/api/resume/index', {
            method: 'POST'
        });
        if (response.ok) {
            getFilesStatus();
            setIsModalOpen(false);
        }
    }

    const getGitProfiles = async () => {
        setModalDescription("Retrieving & summarizing profiles");
        setIsModalOpen(true)
        const response = await fetch('http://127.0.0.1:8000/api/resume/resumes', {
            method: 'GET'
        });
        if (response.ok) {
            const body = await response.json();
            setGithubs(body);
            setIsModalOpen(false);
        }
    }

    return (
        <div className="flex flex-col gap-8 w-[75%]">
            {
                isLoading ? <Spinner className='mx-auto'/> :
                    <div className='flex gap-8'>
                        <Textarea
                            label='Indexed Files'
                            labelPlacement='outside'
                            maxRows={5}
                            value={indexedFiles.join('\n')}
                            readOnly
                        />
                        <Textarea
                            label='Files to be Indexed'
                            labelPlacement='outside'
                            maxRows={5}
                            value={toIndex.join('\n')}
                            readOnly
                        />
                    </div>
            }
            <div className='flex items-center justify-between'>
                <label
                    className="self-center w-fit flex items-center text-white pointer-events-auto cursor-pointer bg-blue-nextUi px-4 py-2 rounded-2xl">
                    <input
                        type="file"
                        onChange={handleFileUpload}
                        multiple
                        className="hidden"
                        ref={fileInputRef}
                    />
                    <div className="mr-2 pb-2">
                        <UploadPhoto height={24} width={24}/>
                    </div>
                    Upload Files
                </label>
                <Button color='primary' size='lg' onClick={startIndex}>Index</Button>
            </div>
            <Textarea
                label='Job description'
                isRequired
                maxRows={5}
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
            />
            <Input
                label='Number of resumes to recommend'
                type='number'
                value={numberToRetrieve.toString()}
                isRequired
                onChange={(e) => setNumberToRetrieve(parseInt(e.target.value))}
            />
            <div className='flex justify-between'>
                <Button color='primary' onClick={() => retrieve('simple')}>Simple Matching</Button>
                <Button color='primary' onClick={() => retrieve('reranked')}>Reranked Matching</Button>
                <Button color='primary' onClick={() => getGitProfiles()}>Github Profiles</Button>
                {/*<Button color='primary' isDisabled>LLM Matching</Button>*/}
            </div>
            {resumes.length > 0 &&
                <>
                    <p className='text-lg font-semibold mt-4'>Resumes</p>
                    <div className='border-solid border-2 rounded-md border-gray-300 mt-1 p-2'>
                        <Accordion selectionMode="multiple">
                            {
                                resumes.map((resume, index) =>
                                    <AccordionItem key={index} aria-label={resume.file_name} title={<p className='text-blue-600'>{resume.file_name}</p>}>
                                        <p className='whitespace-pre-line'>{resume.content}</p>
                                    </AccordionItem>
                                )
                            }
                        </Accordion>
                    </div>
                </>
            }
            {githubs.length > 0 &&
                <>
                    <p className='text-lg font-semibold mt-4'>Github Profiles</p>
                    <div className='border-solid border-2 rounded-md border-gray-300 mt-1 p-2'>
                        <Accordion selectionMode="multiple">
                            {
                                githubs.map((profile, index) =>
                                    <AccordionItem key={index} aria-label={profile.username}
                                                   title={<a target='_blank' className='text-blue-600'
                                                             href={`https://github.com/${profile.username}`}>{profile.username}</a>}>
                                        <div className='flex flex-col gap-4 px-4'>
                                            <p className='text-lg font-semibold'>Summarized Projects</p>
                                            {
                                                profile.descriptions.map((desc: string, index: number) =>
                                                    <p className='whitespace-pre-line' key={index}><b>{index + 1}: </b>{desc} </p>)
                                            }
                                            <p className='text-lg font-semibold'>Analysis</p>
                                            <p className='pb-4 whitespace-pre-line'>{profile.analysis}</p>
                                            {/*<p className='pb-4'><b>Filename:</b> {profile.file_name}</p>*/}
                                        </div>
                                    </AccordionItem>
                                )
                            }
                        </Accordion>
                    </div>
                </>
            }
            <Modal isOpen={isModalOpen} isDismissable={false} hideCloseButton={true}>
                <ModalContent>
                    <ModalHeader className="mx-auto">{modalDescription}</ModalHeader>
                    <ModalBody className='p-4'>
                        <Spinner/>
                    </ModalBody>
                </ModalContent>
            </Modal>
        </div>
    )
}

export default ResumeMatcher;