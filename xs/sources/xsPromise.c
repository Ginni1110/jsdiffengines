/*
 * Copyright (c) 2016-2017  Moddable Tech, Inc.
 *
 *   This file is part of the Moddable SDK Runtime.
 * 
 *   The Moddable SDK Runtime is free software: you can redistribute it and/or modify
 *   it under the terms of the GNU Lesser General Public License as published by
 *   the Free Software Foundation, either version 3 of the License, or
 *   (at your option) any later version.
 * 
 *   The Moddable SDK Runtime is distributed in the hope that it will be useful,
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *   GNU Lesser General Public License for more details.
 * 
 *   You should have received a copy of the GNU Lesser General Public License
 *   along with the Moddable SDK Runtime.  If not, see <http://www.gnu.org/licenses/>.
 *
 * This file incorporates work covered by the following copyright and  
 * permission notice:  
 *
 *       Copyright (C) 2010-2016 Marvell International Ltd.
 *       Copyright (C) 2002-2010 Kinoma, Inc.
 *
 *       Licensed under the Apache License, Version 2.0 (the "License");
 *       you may not use this file except in compliance with the License.
 *       You may obtain a copy of the License at
 *
 *        http://www.apache.org/licenses/LICENSE-2.0
 *
 *       Unless required by applicable law or agreed to in writing, software
 *       distributed under the License is distributed on an "AS IS" BASIS,
 *       WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *       See the License for the specific language governing permissions and
 *       limitations under the License.
 */

#include "xsAll.h"

//#define mxPromisePrint 1

static void fxCombinePromises(txMachine* the, txInteger which);
static void fxCombinePromisesCallback(txMachine* the);
static txSlot* fxNewCombinePromisesFunction(txMachine* the, txInteger which, txSlot* already, txSlot* object);
static void fxRejectPromise(txMachine* the);
static void fxResolvePromise(txMachine* the);

static void fx_Promise_resolveAux(txMachine* the);
static void fx_Promise_prototype_finallyAux(txMachine* the);
static void fx_Promise_prototype_finallyReturn(txMachine* the);
static void fx_Promise_prototype_finallyThrow(txMachine* the);

enum {
	XS_PROMISE_COMBINE_NONE = 0,
	XS_PROMISE_COMBINE_FULFILLED = 1,
	XS_PROMISE_COMBINE_REJECTED = 2,
	XS_PROMISE_COMBINE_SETTLED = 4,
};

void fxBuildPromise(txMachine* the)
{
	txSlot* slot;
	mxPush(mxObjectPrototype);
	slot = fxLastProperty(the, fxNewObjectInstance(the));
	slot = fxNextHostFunctionProperty(the, slot, mxCallback(fx_Promise_prototype_catch), 1, mxID(_catch), XS_DONT_ENUM_FLAG);
	slot = fxNextHostFunctionProperty(the, slot, mxCallback(fx_Promise_prototype_finally), 1, mxID(_finally_), XS_DONT_ENUM_FLAG);
	slot = fxNextHostFunctionProperty(the, slot, mxCallback(fx_Promise_prototype_then), 2, mxID(_then), XS_DONT_ENUM_FLAG);
	slot = fxNextStringXProperty(the, slot, "Promise", mxID(_Symbol_toStringTag), XS_DONT_ENUM_FLAG | XS_DONT_SET_FLAG);
	mxPromisePrototype = *the->stack;
	slot = fxBuildHostConstructor(the, mxCallback(fx_Promise), 1, mxID(_Promise));
	mxPromiseConstructor = *the->stack;
	slot = fxLastProperty(the, slot);
	slot = fxNextHostFunctionProperty(the, slot, mxCallback(fx_Promise_all), 1, mxID(_all), XS_DONT_ENUM_FLAG);
	slot = fxNextHostFunctionProperty(the, slot, mxCallback(fx_Promise_allSettled), 1, mxID(_allSettled), XS_DONT_ENUM_FLAG);
	slot = fxNextHostFunctionProperty(the, slot, mxCallback(fx_Promise_any), 1, mxID(_any), XS_DONT_ENUM_FLAG);
	slot = fxNextHostFunctionProperty(the, slot, mxCallback(fx_Promise_race), 1, mxID(_race), XS_DONT_ENUM_FLAG);
	slot = fxNextHostFunctionProperty(the, slot, mxCallback(fx_Promise_reject), 1, mxID(_reject), XS_DONT_ENUM_FLAG);
	slot = fxNextHostFunctionProperty(the, slot, mxCallback(fx_Promise_resolve), 1, mxID(_resolve), XS_DONT_ENUM_FLAG);
	slot = fxNextHostAccessorProperty(the, slot, mxCallback(fx_species_get), C_NULL, mxID(_Symbol_species), XS_DONT_ENUM_FLAG);
	the->stack++;
	fxNewHostFunction(the, mxCallback(fxOnRejectedPromise), 1, XS_NO_ID);
	mxOnRejectedPromiseFunction = *the->stack;
	the->stack++;
	fxNewHostFunction(the, mxCallback(fxOnResolvedPromise), 1, XS_NO_ID);
	mxOnResolvedPromiseFunction = *the->stack;
	the->stack++;
	fxNewHostFunction(the, mxCallback(fxOnThenable), 1, XS_NO_ID);
	mxOnThenableFunction = *the->stack;
	the->stack++;
}

txSlot* fxNewPromiseInstance(txMachine* the)
{
#ifdef mxPromisePrint
	static txID gID = 0;
#endif
	txSlot* promise;
	txSlot* slot;
	txSlot* instance;
	promise = fxNewSlot(the);
	promise->kind = XS_INSTANCE_KIND;
	promise->value.instance.garbage = C_NULL;
	promise->value.instance.prototype = the->stack->value.reference;
	the->stack->kind = XS_REFERENCE_KIND;
	the->stack->value.reference = promise;
	/* STATUS */
	slot = promise->next = fxNewSlot(the);
	slot->flag = XS_INTERNAL_FLAG | XS_DONT_DELETE_FLAG | XS_DONT_ENUM_FLAG | XS_DONT_SET_FLAG;
#ifdef mxPromisePrint
	slot->ID = gID++;
#endif
	slot->kind = XS_PROMISE_KIND;
	slot->value.integer = mxUndefinedStatus;
	/* THENS */
	slot = slot->next = fxNewSlot(the);
	slot->flag = XS_INTERNAL_FLAG | XS_DONT_DELETE_FLAG | XS_DONT_ENUM_FLAG | XS_DONT_SET_FLAG;
	slot->value.reference = instance = fxNewSlot(the);
    slot->kind = XS_REFERENCE_KIND;
	instance->kind = XS_INSTANCE_KIND;
	instance->value.instance.garbage = C_NULL;
	instance->value.instance.prototype = C_NULL;
	/* RESULT */
	slot = slot->next = fxNewSlot(the);
	slot->flag = XS_INTERNAL_FLAG | XS_DONT_DELETE_FLAG | XS_DONT_ENUM_FLAG | XS_DONT_SET_FLAG;
	return promise;
}

void fxBuildPromiseCapability(txMachine* the)
{
	txSlot* slot = mxFunctionInstanceHome(mxFunction->value.reference);
	txSlot* object = slot->value.home.object;
	txSlot* resolveFunction;
	txSlot* rejectFunction;
	if (object) {
		resolveFunction = object->next;
		rejectFunction = resolveFunction->next;
		if (!mxIsUndefined(resolveFunction) || !mxIsUndefined(rejectFunction))
			mxTypeError("executor already called");
	}
	else {
		object = fxNewInstance(the);
		resolveFunction = object->next = fxNewSlot(the);
		rejectFunction = resolveFunction->next = fxNewSlot(the);
		slot->value.home.object = object;
        mxPop();
	}
	if (mxArgc > 0) {
		resolveFunction->kind = mxArgv(0)->kind;
		resolveFunction->value = mxArgv(0)->value;
	}
	if (mxArgc > 1) {
		rejectFunction->kind = mxArgv(1)->kind;
		rejectFunction->value = mxArgv(1)->value;
	}
}

void fxCheckPromiseCapability(txMachine* the, txSlot* capability, txSlot** resolveFunction, txSlot** rejectFunction)
{
	txSlot* slot = mxFunctionInstanceHome(capability)->value.home.object;
	txSlot* function;
	if (!slot)
		mxTypeError("executor not called");
	slot = slot->next;
	if (!mxIsReference(slot))
		mxTypeError("resolve is no object");
	function = slot->value.reference;	
	if (!mxIsFunction(function))
		mxTypeError("resolve is no function");
	*resolveFunction = function;
	slot = slot->next;
	if (!mxIsReference(slot))
		mxTypeError("reject is no object");
	function = slot->value.reference;	
	if (!mxIsFunction(function))
		mxTypeError("reject is no function");
	*rejectFunction = function;
}

void fxCombinePromises(txMachine* the, txInteger which)
{
	txSlot* stack = the->stack;
	txSlot* capability;
	txSlot* promise;
	txSlot* resolveFunction;
	txSlot* rejectFunction;
	txSlot* object;
	txSlot* property;
	txSlot* array;
	txSlot* already;
	txSlot* iterator;
	txInteger index;
	txSlot* result;
	txSlot* argument;
	
	if (!mxIsReference(mxThis))
		mxTypeError("this is no object");
	capability = fxNewHostFunction(the, fxBuildPromiseCapability, 2, XS_NO_ID);
	mxPushReference(capability);
	mxPushInteger(1);
	mxPushSlot(mxThis);
	fxNew(the);
	mxPullSlot(mxResult);
    promise = mxResult->value.reference;
	fxCheckPromiseCapability(the, capability, &resolveFunction, &rejectFunction);
	{
		mxTry(the) {
			if (which) {
				object = fxNewInstance(the);
				property = fxNextIntegerProperty(the, object, 0, XS_NO_ID, XS_NO_FLAG);
				mxPush(mxArrayPrototype);
				array = fxNewArrayInstance(the);
				already = array->next;
				property = fxNextReferenceProperty(the, property, array, XS_NO_ID, XS_NO_FLAG);
				mxPop();
				property = fxNextReferenceProperty(the, property, promise, XS_NO_ID, XS_NO_FLAG);
				if (which == XS_PROMISE_COMBINE_REJECTED)
					property = fxNextReferenceProperty(the, property, rejectFunction, XS_NO_ID, XS_NO_FLAG);
				else
					property = fxNextReferenceProperty(the, property, resolveFunction, XS_NO_ID, XS_NO_FLAG);
			}
			
			if (!mxIsReference(mxArgv(0)))
				mxTypeError("iterable is no object");
			mxPushInteger(0);
			mxPushSlot(mxArgv(0));
			fxCallID(the, mxID(_Symbol_iterator));
			iterator = the->stack;
			index = 0;
			{
				volatile txBoolean close;
				txSlot* resolve;
				mxTry(the) {
					close = 1;
					mxPushSlot(mxThis);
					fxGetID(the, mxID(_resolve));	
					resolve = the->stack;
					for(;;) {
						close = 0;
						mxPushInteger(0);
						mxPushSlot(iterator);
						fxCallID(the, mxID(_next));
						result = the->stack;
						mxPushSlot(result);
						fxGetID(the, mxID(_done));	
						if (fxToBoolean(the, the->stack))
							break;
						mxPushSlot(result);
						fxGetID(the, mxID(_value));	
						close = 1;
						mxPushInteger(1);
						mxPushSlot(mxThis);
						mxPushSlot(resolve);
						fxCall(the);
						argument = the->stack;
						if (which) {
							already = already->next = fxNewSlot(the);
							already->kind = XS_UNINITIALIZED_KIND;
							array->next->value.array.length++;
						}
						if (which & XS_PROMISE_COMBINE_SETTLED) {
							fxNewCombinePromisesFunction(the, which | XS_PROMISE_COMBINE_FULFILLED, already, object);
							fxNewCombinePromisesFunction(the, which | XS_PROMISE_COMBINE_REJECTED, already, object);
						}
						else if (which & XS_PROMISE_COMBINE_FULFILLED) {
							fxNewCombinePromisesFunction(the, which, already, object);
							mxPushReference(rejectFunction);
						}
						else if (which & XS_PROMISE_COMBINE_REJECTED) {
							mxPushReference(resolveFunction);
							fxNewCombinePromisesFunction(the, which, already, object);
						}
						else {
							mxPushReference(resolveFunction);
							mxPushReference(rejectFunction);
						}
						mxPushInteger(2);
						mxPushSlot(argument);
						fxCallID(the, mxID(_then));
						the->stack = resolve;
						index++;
					}
				}
				mxCatch(the) {
					if (close)
						fxCloseIterator(the, iterator);
					fxJump(the);
				}
			}
			if (which) {
				property = object->next;
				property->value.integer += index;
				index = property->value.integer;
			}
			if (index == 0) {
				if ((which == XS_PROMISE_COMBINE_SETTLED) || (which == XS_PROMISE_COMBINE_FULFILLED)) {
					fxCacheArray(the, array);
					mxPushReference(array);
					/* COUNT */
					mxPushInteger(1);
					/* THIS */
					mxPushUndefined();
					mxPushReference(resolveFunction);
				}
				else {
					mxPushUndefined();
					mxPushInteger(1);
					mxPushUndefined();
					if (which == XS_PROMISE_COMBINE_REJECTED)
						mxPushReference(rejectFunction);
					else
						mxPushReference(resolveFunction);
				}
				fxCall(the);
			}
		}
		mxCatch(the) {
			mxPush(mxException);
			mxException = mxUndefined;
			/* COUNT */
			mxPushInteger(1);
			/* THIS */
			mxPushUndefined();
			/* FUNCTION */
			mxPushReference(rejectFunction);
			fxCall(the);
		}
	}
	the->stack = stack;
}

void fxCombinePromisesCallback(txMachine* the)
{
	txSlot* slot = mxFunctionInstanceHome(mxFunction->value.reference)->value.home.object->next;
	txInteger which = slot->value.integer;
	txSlot* instance;
	txSlot* property;
	slot = slot->next;
	if (slot->value.closure->kind != XS_UNINITIALIZED_KIND)
		return;
	if (which & XS_PROMISE_COMBINE_SETTLED) {
		mxPush(mxObjectPrototype);
		instance = fxNewObjectInstance(the);
	}
	if (mxArgc > 0)
		mxPushSlot(mxArgv(0));
	else
		mxPushUndefined();
	if (which & XS_PROMISE_COMBINE_SETTLED) {
		property = fxLastProperty(the, instance);
		if (which & XS_PROMISE_COMBINE_FULFILLED) {
			property = fxNextStringXProperty(the, property, "fulfilled", mxID(_status), XS_NO_FLAG);
			property = fxNextSlotProperty(the, property, the->stack, mxID(_value), XS_NO_FLAG);
		}
		else {
			property = fxNextStringXProperty(the, property, "rejected", mxID(_status), XS_NO_FLAG);
			property = fxNextSlotProperty(the, property, the->stack, mxID(_reason), XS_NO_FLAG);
		}
		mxPop();
	}
	mxPullSlot(slot->value.closure);
	slot = slot->next->value.reference->next;
	slot->value.integer--;
	if (slot->value.integer == 0) {
		slot = slot->next;
		fxCacheArray(the, slot->value.reference);
		mxPushSlot(slot);
		if (which == XS_PROMISE_COMBINE_REJECTED) {
			mxPushInteger(1);
			mxPush(mxAggregateErrorConstructor);
			fxNew(the);
		}
		/* COUNT */
		mxPushInteger(1);
		/* THIS */
		slot = slot->next;
		mxPushSlot(slot);
		/* FUNCTION */
		slot = slot->next;
		mxPushSlot(slot);
		fxCall(the);
		mxPullSlot(mxResult);
	}
}

txSlot* fxNewCombinePromisesFunction(txMachine* the, txInteger which, txSlot* already, txSlot* object)
{
	txSlot* result;
	txSlot* instance;
	txSlot* property;
	result = fxNewHostFunction(the, fxCombinePromisesCallback, 1, XS_NO_ID);
	instance = fxNewInstance(the);
	property = fxNextIntegerProperty(the, instance, which, XS_NO_ID, XS_NO_FLAG);
	property = property->next = fxNewSlot(the);
	property->kind = XS_CLOSURE_KIND;
	property->value.closure = already;
	property = fxNextReferenceProperty(the, property, object, XS_NO_ID, XS_NO_FLAG);
	property = mxFunctionInstanceHome(result);
	property->value.home.object = instance;
	the->stack++;
	return result;
}

void fxOnRejectedPromise(txMachine* the)
{
	txSlot* reaction = mxThis->value.reference;
	txSlot* resolveFunction = reaction->next;
	txSlot* rejectFunction = resolveFunction->next;
	txSlot* resolveHandler = rejectFunction->next;
	txSlot* rejectHandler = resolveHandler->next;
	txSlot* argument = mxArgv(0);
	txSlot* function = rejectFunction;
	if (rejectHandler->kind == XS_REFERENCE_KIND) {
		mxTry(the) {
			mxPushSlot(argument);
			/* COUNT */
			mxPushInteger(1);
			/* THIS */
			mxPushUndefined();
			/* FUNCTION */
			mxPushSlot(rejectHandler);
			fxCall(the);
			mxPullSlot(argument);
			function = resolveFunction;
		}
		mxCatch(the) {
			*argument = mxException;
			mxException = mxUndefined;
		}
	}
    if (function->kind == XS_REFERENCE_KIND) {
		mxPushSlot(argument);
		/* COUNT */
		mxPushInteger(1);
		/* THIS */
		mxPushUndefined();
		/* FUNCTION */
		mxPushSlot(function);
		fxCall(the);
		the->stack++;
	}
}

void fxOnResolvedPromise(txMachine* the)
{
	txSlot* reaction = mxThis->value.reference;
	txSlot* resolveFunction = reaction->next;
	txSlot* rejectFunction = resolveFunction->next;
	txSlot* resolveHandler = rejectFunction->next;
	txSlot* argument = mxArgv(0);
	txSlot* function = resolveFunction;
	if (resolveHandler->kind == XS_REFERENCE_KIND) {
		mxTry(the) {
			mxPushSlot(argument);
			/* COUNT */
			mxPushInteger(1);
			/* THIS */
			mxPushUndefined();
			/* FUNCTION */
			mxPushSlot(resolveHandler);
			fxCall(the);
			mxPullSlot(argument);
		}
		mxCatch(the) {
			*argument = mxException;
			mxException = mxUndefined;
			function = rejectFunction;
		}
	}
    if (function->kind == XS_REFERENCE_KIND) {
        mxPushSlot(argument);
        /* COUNT */
        mxPushInteger(1);
        /* THIS */
        mxPushUndefined();
        /* FUNCTION */
        mxPushSlot(function);
        fxCall(the);
        the->stack++;
    }
}

void fxOnThenable(txMachine* the)
{
	txSlot* resolveFunction = mxArgv(0);
	txSlot* rejectFunction = mxArgv(1);
	txSlot* thenFunction = mxArgv(2);
	mxTry(the) {
		mxPushSlot(resolveFunction);
		mxPushSlot(rejectFunction);
		/* COUNT */
		mxPushInteger(2);
		/* THIS */
		mxPushSlot(mxThis);
		/* FUNCTION */
		mxPushSlot(thenFunction);
		fxCall(the);
		mxPop();
	}
	mxCatch(the) {
		mxPush(mxException);
		mxException = mxUndefined;
		/* COUNT */
		mxPushInteger(1);
		/* THIS */
		mxPushUndefined();
		/* FUNCTION */
		mxPushSlot(rejectFunction);
		fxCall(the);
		the->stack++;
	}
}

void fxPromiseThen(txMachine* the, txSlot* promise, txSlot* onFullfilled, txSlot* onRejected, txSlot* capability)
{
	txSlot* resolveFunction;
	txSlot* rejectFunction;
	txSlot* reaction;
	txSlot* slot;
	txSlot* status;
	
	if (capability)
		fxCheckPromiseCapability(the, capability, &resolveFunction, &rejectFunction);
	reaction = fxNewInstance(the);
	slot = reaction->next = fxNewSlot(the);
	if (capability) {
		slot->kind = XS_REFERENCE_KIND;
		slot->value.reference = resolveFunction;
	}
	slot = slot->next = fxNewSlot(the);
	if (capability) {
		slot->kind = XS_REFERENCE_KIND;
		slot->value.reference = rejectFunction;
	}
	slot = slot->next = fxNewSlot(the);
	if (onFullfilled) {
		slot->kind = onFullfilled->kind;
		slot->value = onFullfilled->value;
	}
	slot = slot->next = fxNewSlot(the);
	if (onRejected) {
		slot->kind = onRejected->kind;
		slot->value = onRejected->value;
	}
		
	status = mxPromiseStatus(promise);
	if (status->value.integer == mxPendingStatus) {
		txSlot** address = &(mxPromiseThens(promise)->value.reference->next);
		while ((slot = *address)) 
			address = &(slot->next);
		slot = *address = fxNewSlot(the);
		slot->kind = XS_REFERENCE_KIND;
		slot->value.reference = reaction;
	}
	else {
		mxPushReference(reaction);
		if (status->value.integer == mxFulfilledStatus)
			mxPush(mxOnResolvedPromiseFunction);
		else
			mxPush(mxOnRejectedPromiseFunction);
		slot = mxPromiseResult(promise);
		mxPushSlot(slot);
		mxPushInteger(1);
		fxQueueJob(the, promise->next->ID);
	}
	mxPop(); // reaction
}

void fxPushPromiseFunctions(txMachine* the, txSlot* promise)
{
	txSlot* resolve;
	txSlot* reject;
	txSlot* object;
	txSlot* slot;
	resolve = fxNewHostFunction(the, fxResolvePromise, 1, XS_NO_ID);
	reject = fxNewHostFunction(the, fxRejectPromise, 1, XS_NO_ID);
	slot = object = fxNewInstance(the);
	slot = object->next = fxNewSlot(the);
	slot->kind = XS_BOOLEAN_KIND;
	slot->value.boolean = 0;
	slot = slot->next = fxNewSlot(the);
	slot->kind = XS_REFERENCE_KIND;
	slot->value.reference = promise;
	slot = mxFunctionInstanceHome(resolve);
	slot->value.home.object = object;
	slot = mxFunctionInstanceHome(reject);
	slot->value.home.object = object;
	mxPop();
}


void fxRejectPromise(txMachine* the)
{
	txSlot* slot;
	txSlot* promise;
	txSlot* argument;
	txSlot* result;
	slot = mxFunctionInstanceHome(mxFunction->value.reference)->value.home.object->next;
	if (slot->value.boolean)
		return;
	slot->value.boolean = 1;
	slot = slot->next;
	promise = slot->value.reference;
	if (mxArgc > 0)
		mxPushSlot(mxArgv(0));
	else
		mxPushUndefined();
	argument = the->stack;
#ifdef mxPromisePrint
	fprintf(stderr, "fxRejectPromise %d\n", promise->next->ID);
#endif
	result = mxPromiseResult(promise);
	result->kind = argument->kind;
	result->value = argument->value;
	slot = mxPromiseThens(promise)->value.reference->next;
	while (slot) {
		mxPushReference(slot->value.reference);
		mxPush(mxOnRejectedPromiseFunction);
		mxPushSlot(argument);
		mxPushInteger(1);
		fxQueueJob(the, promise->next->ID);
		slot = slot->next;
	}
	slot = mxPromiseStatus(promise);
	slot->value.integer = mxRejectedStatus;
}

void fxResolvePromise(txMachine* the)
{
	txSlot* slot;
	txSlot* promise;
	txSlot* argument;
	txSlot* result;
	slot = mxFunctionInstanceHome(mxFunction->value.reference)->value.home.object->next;
	if (slot->value.boolean)
		return;
	slot->value.boolean = 1;
	slot = slot->next;
	promise = slot->value.reference;
	if (mxArgc > 0)
		mxPushSlot(mxArgv(0));
	else
		mxPushUndefined();
	argument = the->stack;	
#ifdef mxPromisePrint
	fprintf(stderr, "fxResolvePromise %d\n", promise->next->ID);
#endif
	mxTry(the) {
		if (mxIsReference(argument)) {
			if (argument->value.reference == promise)
				mxTypeError("promise resolves itself");
			mxPushSlot(argument);
			fxGetID(the, mxID(_then));
			slot = the->stack;
			if (fxIsCallable(the, slot)) {
#ifdef mxPromisePrint
	fprintf(stderr, "fxResolvePromise then %d\n", promise->next->ID);
#endif
				mxPushSlot(argument);
				mxPush(mxOnThenableFunction);
				fxPushPromiseFunctions(the, promise);
				mxPushSlot(slot);
				mxPushInteger(3);
				fxQueueJob(the, promise->next->ID);
				goto bail;
			}
			mxPop();
		}
		result = mxPromiseResult(promise);
		result->kind = argument->kind;
		result->value = argument->value;
		slot = mxPromiseThens(promise)->value.reference->next;
		while (slot) {
			mxPushReference(slot->value.reference);
			mxPush(mxOnResolvedPromiseFunction);
			mxPushSlot(result);
			mxPushInteger(1);
			fxQueueJob(the, promise->next->ID);
			slot = slot->next;
		}
		slot = mxPromiseStatus(promise);
		slot->value.integer = mxFulfilledStatus;
	}
bail:
	mxCatch(the) {
		result = mxPromiseResult(promise);
		result->kind = mxException.kind;
		result->value = mxException.value;
		mxException = mxUndefined;
		slot = mxPromiseThens(promise)->value.reference->next;
		while (slot) {
			mxPushReference(slot->value.reference);
			mxPush(mxOnRejectedPromiseFunction);
			mxPushSlot(result);
			mxPushInteger(1);
			fxQueueJob(the, promise->next->ID);
			slot = slot->next;
		}
		slot = mxPromiseStatus(promise);
		slot->value.integer = mxRejectedStatus;
	}
}

void fx_Promise(txMachine* the)
{
	txSlot* stack = the->stack;
	txSlot* promise;
	txSlot* argument;
	txSlot* status;
	txSlot* resolveFunction;
	txSlot* rejectFunction;
	if (mxIsUndefined(mxTarget))
		mxTypeError("call: Promise");
	if (mxArgc < 1)
		mxTypeError("no executor parameter");
	argument = mxArgv(0);
	if (!fxIsCallable(the, argument))
		mxTypeError("executor is no function");
	mxPushSlot(mxTarget);
	fxGetPrototypeFromConstructor(the, &mxPromisePrototype);
	promise = fxNewPromiseInstance(the);
#ifdef mxPromisePrint
	fprintf(stderr, "fx_Promise %d\n", promise->next->ID);
#endif
	mxPullSlot(mxResult);
	status = mxPromiseStatus(promise);
	status->value.integer = mxPendingStatus;
	fxPushPromiseFunctions(the, promise);
	resolveFunction = the->stack + 1;
	rejectFunction = the->stack;
	{
		mxTry(the) {
			mxPushSlot(resolveFunction);
			mxPushSlot(rejectFunction);
			/* COUNT */
			mxPushInteger(2);
			/* THIS */
			mxPushUndefined();
			/* FUNCTION */
			mxPushSlot(argument);
			fxCall(the);
		}
		mxCatch(the) {
			mxPush(mxException);
			mxException = mxUndefined;
			/* COUNT */
			mxPushInteger(1);
			/* THIS */
			mxPushUndefined();
			/* FUNCTION */
			mxPushSlot(rejectFunction);
			fxCall(the);
		}
	}
	the->stack = stack;
}

void fx_Promise_all(txMachine* the)
{
	fxCombinePromises(the, XS_PROMISE_COMBINE_FULFILLED);
}

void fx_Promise_allSettled(txMachine* the)
{
	fxCombinePromises(the, XS_PROMISE_COMBINE_SETTLED);
}

void fx_Promise_any(txMachine* the)
{
	fxCombinePromises(the, XS_PROMISE_COMBINE_REJECTED);
}

void fx_Promise_race(txMachine* the)
{
	fxCombinePromises(the, XS_PROMISE_COMBINE_NONE);
}

void fx_Promise_reject(txMachine* the)
{
	txSlot* capability;
	txSlot* resolveFunction;
	txSlot* rejectFunction;

	if (!mxIsReference(mxThis))
		mxTypeError("this is no object");
	capability = fxNewHostFunction(the, fxBuildPromiseCapability, 2, XS_NO_ID);
	mxPushReference(capability);
	mxPushInteger(1);
	mxPushSlot(mxThis);
	fxNew(the);
	mxPullSlot(mxResult);
	fxCheckPromiseCapability(the, capability, &resolveFunction, &rejectFunction);
	if (mxArgc > 0)
		mxPushSlot(mxArgv(0));
	else
		mxPushUndefined();
	/* COUNT */
	mxPushInteger(1);
	/* THIS */
	mxPushUndefined();
	/* FUNCTION */
	mxPushReference(rejectFunction);
	fxCall(the);
	mxPop();
	mxPop(); // capability
}

void fx_Promise_resolve(txMachine* the)
{
	if (!mxIsReference(mxThis))
		mxTypeError("this is no object");
	mxPushSlot(mxThis);
	if (mxArgc > 0)
		mxPushSlot(mxArgv(0));
	else
		mxPushUndefined();
	fx_Promise_resolveAux(the);		
	mxPop();
	mxPop();
}

void fx_Promise_resolveAux(txMachine* the)
{
	txSlot* argument = the->stack;
	txSlot* constructor = the->stack + 1;
	txSlot* capability;
	txSlot* resolveFunction;
	txSlot* rejectFunction;
// 	if (!mxIsReference(mxThis))
// 		mxTypeError("this is no object");
	if (mxIsReference(argument)) {
		txSlot* promise = argument->value.reference;
		if (mxIsPromise(promise)) {
			mxPushReference(promise);
			fxGetID(the, mxID(_constructor));
			if (fxIsSameValue(the, constructor, the->stack, 0)) {
				*mxResult = *argument;
				return;
			}
			mxPop();
		}
	}
	capability = fxNewHostFunction(the, fxBuildPromiseCapability, 2, XS_NO_ID);
	mxPushReference(capability);
	mxPushInteger(1);
	mxPushSlot(constructor);
	fxNew(the);
	mxPullSlot(mxResult);
	fxCheckPromiseCapability(the, capability, &resolveFunction, &rejectFunction);
	mxPushSlot(argument);
	/* COUNT */
	mxPushInteger(1);
	/* THIS */
	mxPushUndefined();
	/* FUNCTION */
	mxPushReference(resolveFunction);
	fxCall(the);
	mxPop();
	mxPop(); // capability
}

void fx_Promise_prototype_catch(txMachine* the)
{
	mxPushUndefined();
	if (mxArgc > 0) 
		mxPushSlot(mxArgv(0));
	else
		mxPushUndefined();
	mxPushInteger(2);
	mxPushSlot(mxThis);
	fxCallID(the, mxID(_then));
	mxPullSlot(mxResult);
}

#if 0
void fx_Promise_prototype_dumpAux(txMachine* the, txSlot* promise, txInteger c)
{
	txInteger i;
	txSlot* reference;
	for (i = 0; i < c; i++)
		fprintf(stderr, "\t");
	fprintf(stderr, "promise %d\n", promise->next->ID);
	reference = mxPromiseThens(promise)->value.reference->next;
    c++;
	while (reference) {
		fx_Promise_prototype_dumpAux(the, reference->value.reference, c);
		reference = reference->next;
	}
}
#endif

void fx_Promise_prototype_finally(txMachine* the)
{
	txSlot* constructor;
	if (!mxIsReference(mxThis))
		mxTypeError("this is no object");
	mxPushSlot(mxThis);
	fxGetID(the, mxID(_constructor));
	fxToSpeciesConstructor(the, &mxPromiseConstructor);
	constructor = the->stack;
	if (mxArgc > 0) {
		if (mxIsReference(mxArgv(0)) && mxIsCallable(mxArgv(0)->value.reference)) {
			txSlot* function = fxNewHostFunction(the, fx_Promise_prototype_finallyAux, 1, XS_NO_ID);
			txSlot* object = fxNewInstance(the);
			txSlot* slot = object->next = fxNewSlot(the);
			slot->kind = XS_REFERENCE_KIND;
			slot->value.reference = constructor->value.reference;
			slot = slot->next = fxNewSlot(the);
			slot->kind = XS_REFERENCE_KIND;
			slot->value.reference = mxArgv(0)->value.reference;
			slot = slot->next = fxNewSlot(the);
			slot->kind = XS_BOOLEAN_KIND;
			slot->value.boolean = 1;
			slot = mxFunctionInstanceHome(function);
			slot->value.home.object = object;
			mxPop();
			
			function = fxNewHostFunction(the, fx_Promise_prototype_finallyAux, 1, XS_NO_ID);
			object = fxNewInstance(the);
			slot = object->next = fxNewSlot(the);
			slot->kind = XS_REFERENCE_KIND;
			slot->value.reference = constructor->value.reference;
			slot = slot->next = fxNewSlot(the);
			slot->kind = XS_REFERENCE_KIND;
			slot->value.reference = mxArgv(0)->value.reference;
			slot = slot->next = fxNewSlot(the);
			slot->kind = XS_BOOLEAN_KIND;
			slot->value.boolean = 0;
			slot = mxFunctionInstanceHome(function);
			slot->value.home.object = object;
			mxPop();
		}
		else {
			mxPushSlot(mxArgv(0));
			mxPushSlot(mxArgv(0));
		}
	}
	else {
		mxPushUndefined();
		mxPushUndefined();
	}
	mxPushInteger(2);
	mxPushSlot(mxThis);
	fxCallID(the, mxID(_then));
	mxPullSlot(mxResult);
	mxPop();
}

void fx_Promise_prototype_finallyAux(txMachine* the)
{
	txSlot* object = mxFunctionInstanceHome(mxFunction->value.reference)->value.home.object;
	txSlot* constructor = object->next;
	txSlot* onFinally = constructor->next;
	txSlot* success = onFinally->next;
	txSlot* argument;
	txSlot* function;
	txSlot* slot;
	txSlot* home;
	txSlot* stack;
	
	{
		mxTry(the) {
			mxPushInteger(0);
			mxPushUndefined();
			mxPushSlot(onFinally);
			fxCall(the);
		}
		mxCatch(the) {
			mxArgv(0)->kind = mxException.kind;
			mxArgv(0)->value = mxException.value;
			success->value.boolean = 0;
			mxPush(mxException);
			mxException = mxUndefined;
		}
	}
	argument = the->stack;
	
	if (success->value.boolean)
		function = fxNewHostFunction(the, fx_Promise_prototype_finallyReturn, 0, XS_NO_ID);
	else
		function = fxNewHostFunction(the, fx_Promise_prototype_finallyThrow, 0, XS_NO_ID);
	object = fxNewInstance(the);
	slot = object->next = fxNewSlot(the);
	slot->kind = mxArgv(0)->kind;
	slot->value = mxArgv(0)->value;
	home = mxFunctionInstanceHome(function);
	home->value.home.object = object;
	mxPop();
	mxPushUndefined();
	mxPushInteger(2);
	
	stack = the->stack;
	mxPushSlot(constructor);
	mxPushSlot(argument);
	fx_Promise_resolveAux(the);
	mxPop();
	mxPop();
	the->stack = stack;
    mxPushSlot(mxResult);

	fxCallID(the, mxID(_then));
	mxPullSlot(mxResult);
}

void fx_Promise_prototype_finallyReturn(txMachine* the)
{
	txSlot* object = mxFunctionInstanceHome(mxFunction->value.reference)->value.home.object;
	txSlot* slot = object->next;
	mxResult->kind = slot->kind;
	mxResult->value = slot->value;
}

void fx_Promise_prototype_finallyThrow(txMachine* the)
{
	txSlot* object = mxFunctionInstanceHome(mxFunction->value.reference)->value.home.object;
	txSlot* slot = object->next;
	mxException.kind = slot->kind;
	mxException.value = slot->value;
	fxThrow(the, NULL, 0);
}

void fx_Promise_prototype_then(txMachine* the)
{
	txSlot* promise;
	txSlot* onFullfilled = C_NULL;
	txSlot* onRejected = C_NULL;
	txSlot* capability;

	if (!mxIsReference(mxThis))
		mxTypeError("this is no object");
	promise = mxThis->value.reference;
	if (!mxIsPromise(promise))
		mxTypeError("this is no promise");
#ifdef mxPromisePrint
	fprintf(stderr, "fx_Promise_prototype_then %d\n", promise->next->ID);
#endif

	if ((mxArgc > 0) && mxIsReference(mxArgv(0))) {
		onFullfilled = mxArgv(0);
	}
	if ((mxArgc > 1) && mxIsReference(mxArgv(1))) {
		onRejected = mxArgv(1);
	}
		
	capability = fxNewHostFunction(the, fxBuildPromiseCapability, 2, XS_NO_ID);
	mxPushReference(capability);
	mxPushInteger(1);
	mxPushSlot(mxThis);
	fxGetID(the, mxID(_constructor));
	fxToSpeciesConstructor(the, &mxPromiseConstructor);
	fxNew(the);
	mxPullSlot(mxResult);
		
	fxPromiseThen(the, promise, onFullfilled, onRejected, capability);
	mxPop(); // capability
}

void fxQueueJob(txMachine* the, txID id)
{
	txSlot* job;
	txSlot* stack;
	txSlot* slot;
	txInteger count;
	txSlot** address;
	
	if (mxPendingJobs.value.reference->next == NULL) {
		fxQueuePromiseJobs(the);
	}
#ifdef mxPromisePrint
	fprintf(stderr, "fxQueueJob %d\n", id);
#endif
	job = fxNewInstance(the);
	stack = the->stack + 1;
	count = stack->value.integer;
	stack += 1 + count + 1;
	slot = job->next = fxNewSlot(the);
	slot->kind = stack->kind;
	slot->value = stack->value;
	stack--;
	slot = slot->next = fxNewSlot(the);
	slot->kind = stack->kind;
	slot->value = stack->value;
	stack--;
	while (count > 0) {
		slot = slot->next = fxNewSlot(the);
		slot->kind = stack->kind;
		slot->value = stack->value;
		count--;
		stack--;
	}
	address = &(mxPendingJobs.value.reference->next);
	while ((slot = *address)) 
		address = &(slot->next);
	slot = *address = fxNewSlot(the);	
	slot->kind = XS_REFERENCE_KIND;
	slot->value.reference = job;
	the->stack += 2 + count + 2;
}

void fxRunPromiseJobs(txMachine* the)
{
	txSlot* job;
	txSlot* slot;
	txInteger count;
	
#ifdef mxPromisePrint
	fprintf(stderr, "\n# fxRunPromiseJobs\n");
#endif
	job = mxRunningJobs.value.reference->next = mxPendingJobs.value.reference->next;
	mxPendingJobs.value.reference->next = C_NULL;
	while (job) {
		mxTry(the) {
            /* THIS */
			slot = job->value.reference->next;
			mxPushSlot(slot);
			/* FUNCTION */
			slot = slot->next;
			mxPushSlot(slot);
			/* TARGET */
			mxPushUndefined();
			/* RESULT */
			mxPushUndefined();
			mxPushUndefined();
			mxPushUndefined();
			/* ARGUMENTS */
			count = 0;
			slot = slot->next;
			while (slot) {
				mxPushSlot(slot);
				count++;
				slot = slot->next;
			}
			fxRunID(the, C_NULL, count);
			the->stack++;
			fxEndJob(the);
		}
		mxCatch(the) {
		}
		job = job->next;
	}
	mxRunningJobs.value.reference->next = C_NULL;
}





